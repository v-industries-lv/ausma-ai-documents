import email
import imaplib
from email.header import decode_header
from email.utils import parsedate_to_datetime, parseaddr
import os
import re
import argparse
import yaml
from bs4 import BeautifulSoup
from utils import clean_name

def clean_header(value):
    """Decode headers if needed."""
    if value:
        decoded_bytes, encoding = decode_header(value)[0]
        if isinstance(decoded_bytes, bytes):
            return decoded_bytes.decode(encoding or "utf-8", errors="replace")
        return decoded_bytes
    return ""

def looks_like_html(text):
    return bool(text) and ("<html" in text.lower() or "<body" in text.lower() or "<div" in text.lower())

def normalize_newlines(text):
    # Convert Windows/Mac line endings to \n
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Reduce 3+ consecutive newlines to just 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

def strip_lines(text):
    return '\n'.join(line.strip() for line in text.splitlines())

def clean_email_body(text):
    text = strip_lines(text)
    text = normalize_newlines(text)
    return text.strip()  # Remove leading/trailing blank lines in result

def remove_zero_spaces(text):
    text = re.sub(
        r'[\u200B\u200C\u200D\uFEFF]',
        '',
        text
    )
    return text

def html_to_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup.find_all("script"):
        script.decompose()
    # Optional: Remove <style> tags too (comment next 2 lines if not wanted)
    for style in soup.find_all("style"):
        style.decompose()

    def process_tag(tag):
        # Paragraph
        if tag.name in ('p', 'div'):
            return '\n' + ''.join(process_tag(x) for x in tag.children) + '\n'
        # Headers
        elif tag.name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            level = int(tag.name[1])
            text = ''.join(process_tag(x) for x in tag.children)
            return '\n' + ('#' * level) + ' ' + text.strip() + '\n'
        # Lists
        elif tag.name == 'ul':
            return '\n' + ''.join(process_tag(x) for x in tag.children) + '\n'
        elif tag.name == 'ol':
            return '\n' + ''.join(process_tag(x) for x in tag.children) + '\n'
        elif tag.name == 'li':
            parent = tag.parent
            if parent and parent.name == 'ol':
                # Try to number items (optional: more robust numbering logic could be added)
                items = list(parent.find_all('li', recursive=False))
                num = items.index(tag) + 1 if tag in items else 1
                bullet = f"{num}."
            else:
                bullet = "*"
            return bullet + ' ' + ''.join(process_tag(x) for x in tag.children).strip() + '\n'
        # Links
        elif tag.name == 'a':
            link_text = ''.join(process_tag(x) for x in tag.children).strip()
            href = tag.get('href', '')
            if href:
                return f"{link_text} ({href})"
            else:
                return link_text
        # Line breaks
        elif tag.name == 'br':
            return '\n'
        # Horizontal rule
        elif tag.name == 'hr':
            return '\n---\n'
        # Other tags
        elif hasattr(tag, 'children'):
            return ''.join(process_tag(x) for x in tag.children)
        # Plain strings
        else:
            return str(tag) if tag else ''

    plain = process_tag(soup).strip()

    return clean_email_body(
            remove_zero_spaces(
                plain
            )
        ).strip()


def datestring_to_filename(dt):
    return dt.replace(":", "-").replace(".", "_")


def main(args):
    emails = {}
    if args.use_config:
        if os.path.exists("email_credentials.yaml"):
            with open("email_credentials.yaml", "r") as fh:
                emails = yaml.load(fh, Loader=yaml.SafeLoader)
            if not emails:
                exit("Empty credentials file!")
        else:
            exit("No email credentials. To use credentials file, create email_credentials.yaml following schema:\n"
                 "email:\n"
                 "  host: host\n"
                 "  port: port\n"
                 "  username: username\n"
                 "  password: password\n"
                 "  whitelist: "
                 "    - @domain.name"
                 "    - sender@domain.name")
    else:
        host = args.host if args.host else input("Enter IMAP SSL host: ")
        username = args.usr if args.usr else input("Enter email username: ")
        pw = args.pw if args.pw else input("Enter email password: ")
        emails = {
            username:
                {
                "host": host,
                "port": args.port,
                "username": username,
                "password": pw,
                "whitelist": args.wl.split(";") if args.wl else [],
            }
        }
    for credentials in emails.values():
        mail = imaplib.IMAP4_SSL(credentials['host'])
        mail.login(credentials['username'], credentials['password'])

        # Select the folder
        mail.select('inbox')

        status, messages = mail.search(None, 'ALL')
        email_ids = messages[0].split()

        inbox_folder_name = credentials['username'].replace("@", "_")
        output_folder = os.path.join('emails', inbox_folder_name)
        os.makedirs(output_folder, exist_ok=True)
        attachments_path = os.path.join(output_folder, "attachments")
        os.makedirs(attachments_path, exist_ok=True)
        total_attachments = []

        for eid in email_ids:
            status, msg_data = mail.fetch(eid, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Extract headers
            from_name, from_email = parseaddr(msg.get("From"))

            to_list = msg.get_all("To", [])
            all_recipients = email.utils.getaddresses(to_list)

            to_list = msg.get_all("CC", [])
            all_cc_recipients = email.utils.getaddresses(to_list)

            subject = clean_header(msg.get("Subject"))

            # Extract body (plain text part)
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get("Content-Disposition"))
                    if ctype == "text/plain" and "attachment" not in cdispo:
                        charset = part.get_content_charset() or "utf-8"
                        body = clean_email_body(part.get_payload(decode=True).decode(charset, "replace"))
                        break
            else:
                charset = msg.get_content_charset() or "utf-8"
                body = clean_email_body(msg.get_payload(decode=True).decode(charset, "replace"))

            # Extract attachment info
            attachments = []
            attachment_count = 0
            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get("Content-Disposition"))
                    # Collect attachments only
                    if "attachment" in cdispo.lower():
                        attachment_count += 1
                        filename = part.get_filename()
                        if filename:
                            filename = clean_header(filename)
                            # !!! Decoding for filesize purposes.
                            data = part.get_payload(decode=True)
                            size = len(data) if data else 0
                            if args.save_attachments:
                                email_allowed = False
                                for mail_filter in credentials["whitelist"]:
                                    if mail_filter.startswith("@"):
                                        if mail_filter in from_email:
                                            email_allowed = True
                                            break
                                    else:
                                        if from_email == mail_filter:
                                            email_allowed = True
                                            break
                                if email_allowed:
                                    final_filename = "_".join([eid.decode(), str(attachment_count), filename])
                                    with open(os.path.join(attachments_path, final_filename), "wb") as f:
                                        f.write(data)
                                    total_attachments.append(final_filename)
                            attachments.append( (clean_header(filename), size) )

            # Extract date
            date_str = clean_header(msg.get("Date"))
            if date_str == "":
                formatted_date = "(No date)"
            else:
                try:
                    date_obj = parsedate_to_datetime(date_str)
                    formatted_date = date_obj.isoformat()
                except Exception:
                    formatted_date = date_str

            # Save as plain text
            with open(os.path.join(output_folder, f"{datestring_to_filename(formatted_date)}_{clean_name(subject) if bool(subject) else "(none)"}.txt"), 'w', encoding='utf-8') as f:
                f.write(f"Date: {formatted_date}\n")
                f.write(f"From: {clean_header(from_name)} <{from_email}>\n")

                recipients_string = ", ".join([f"{name} <{address}>" for name, address in all_recipients])
                f.write(f"To: {recipients_string if bool(recipients_string) else "(none)"}\n")

                cc_recipients_string = ", ".join([f"{name} <{address}>" for name, address in all_cc_recipients])
                f.write(f"CC: {cc_recipients_string if bool(cc_recipients_string) else "(none)"}\n")

                f.write(f"Subject: {subject if subject is not None else "(none)"}\n")
                f.write(f"Body:\n{html_to_text(body) if looks_like_html(body) else remove_zero_spaces(body)}\n")
                f.write(f"Attachments:\n")
                if len(attachments) > 0:
                    for filename, size in attachments:
                        size_up = round(size/1024, 1)
                        units = "KB"
                        if size_up > 1024:
                            size_up = round(size_up / 1024, 1)
                            units = "MB"
                        if size_up > 1024:
                            size_up = round(size_up / 1024, 1)
                            units = "GB"

                        f.write(f"  - {filename} ({size_up} {units})\n")
                else:
                    f.write("  (none)\n")

        mail.logout()

        if len(total_attachments) > 0:
            print(f"You have following attachments extracted from emails in address {credentials['username']}:")
            for file in total_attachments:
                print(f"  - {file}")
            print(f"See {attachments_path} for files. Schema - [email_id]_[attachment_number]_[attachment_filename]")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, help='IMAP SSL host')
    parser.add_argument('--port', type=int, help='Which port to use. Default 993', default=993)
    parser.add_argument('--usr', type=str, help='Username for the email')
    parser.add_argument('--pw', type=str, help='Password for the email')
    parser.add_argument('--wl', type=str,
                        help='\';\' separated email whitelist. \\@domain.name to whitelist whole domain.')
    parser.add_argument('--use-config', action='store_true', help='Use email config file')
    parser.add_argument('--save-attachments', action='store_true',
                        help='Save attachments of the email. CAUTION: It is never a good idea to download random attachments from random emails.')

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    main(args)