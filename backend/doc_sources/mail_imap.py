import datetime
import email
import imaplib
import os
import re
import ssl
from email.header import decode_header
from email.utils import parsedate_to_datetime, parseaddr
from typing import Optional, List, Dict, Union

from bs4 import BeautifulSoup
from glob2regex import glob2regex

from convertors.document_file import DocumentFile, TextDocumentFile
from doc_sources.doc_source import DocSource
from logger import logger
from utils import to_posix_path, from_posix_path


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


def save_email_text(raw_email: bytes, email_file_path):
    msg = email.message_from_bytes(raw_email)

    # Extract headers
    from_name, from_email = parseaddr(msg.get("From"))

    to_list = msg.get_all("To", [])
    all_recipients = email.utils.getaddresses(to_list)

    to_list = msg.get_all("CC", [])
    all_cc_recipients = email.utils.getaddresses(to_list)

    subject = clean_header(msg.get("Subject"))

    # Extract body (plain text part)
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
                    attachments.append((clean_header(filename), size))

    # Extract date
    date_str = clean_header(msg.get("Date"))
    if date_str == "":
        formatted_date = "(No date)"
    else:
        try:
            date_obj: Optional[datetime.datetime] = parsedate_to_datetime(date_str)
            formatted_date = date_obj.isoformat()
        except Exception:
            formatted_date = date_str

    # Save as plain text
    with open(email_file_path, 'w', encoding='utf-8') as f:
        f.write(f"Date: {formatted_date}\n")
        f.write(f"From: {clean_header(from_name)} <{from_email}>\n")

        recipients_string = ", ".join([f"{name} <{address}>" for name, address in all_recipients])
        f.write(f"To: {recipients_string if bool(recipients_string) else "(none)"}\n")

        cc_recipients_string = ", ".join([f"{name} <{address}>" for name, address in all_cc_recipients])
        f.write(f"CC: {cc_recipients_string if bool(cc_recipients_string) else "(none)"}\n")

        f.write(f"Subject: {subject if bool(subject) else "(none)"}\n")
        f.write(f"Body:\n{html_to_text(body) if looks_like_html(body) else remove_zero_spaces(body)}\n")
        f.write(f"Attachments:\n")
        if len(attachments) > 0:
            for filename, size in attachments:
                size_up = round(size / 1024, 1)
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


class MailCache:
    MAIL_CACHE_FOLDER = os.path.join(".cache", "mail_cache")

    def __init__(self, host: str, port: int, email: str, pw: str,
                 skip_verify=False):
        self.host: str = host
        self.port: int = port
        self.email: str = email
        self.pw: str = pw

        self.mail_cache = os.path.join(MailCache.MAIL_CACHE_FOLDER, f"{host}_{port}", self.email.replace("@", "_"))
        if not os.path.exists(self.mail_cache):
            os.makedirs(self.mail_cache, exist_ok=True)
        self.ssl_ctx = ssl.create_default_context()
        if skip_verify:
            self.ssl_ctx.check_hostname = False
            self.ssl_ctx.verify_mode = ssl.CERT_NONE
        self.mail_client: Optional[imaplib.IMAP4_SSL] = None
        self.selected_mailbox: Optional[str] = None

    def _connect(self, mailbox=None):
        self.mail_client: imaplib.IMAP4_SSL = imaplib.IMAP4_SSL(self.host, ssl_context=self.ssl_ctx)
        self.mail_client.login(self.email, self.pw)
        if mailbox is not None:
            self.mail_client.select(f'"{mailbox}"', readonly=True)
            self.selected_mailbox = mailbox

    def _ensure_selected_mailbox(self, mailbox):
        if self.mail_client is None:
            self._connect(mailbox)
        try:
            if self.selected_mailbox is not mailbox:
                self.mail_client.select(f'"{mailbox}"', readonly=True)
        except imaplib.IMAP4.abort:
            self._connect(mailbox)
        except Exception as e:
            logger.error(f"[MailCache] {self.email}: {e}")
            raise e

    def list_mailboxes(self) -> List[str]:
        if self.mail_client is None:
            self._connect()

        try:
            status, mailboxes = self.mail_client.list()
        except imaplib.IMAP4.abort:
            self._connect()
            status, mailboxes = self.mail_client.list()
        except imaplib.IMAP4.error:
            return []
        except Exception as e:
            logger.error(f"[MailCache] {self.email}: {e}.")
            raise e

        names = []
        for entry in mailboxes:
            # example from RFC9051
            # (\HasChildren \Subscribed) "/" "Foo"
            # noinspection PyUnresolvedReferences
            line = str(entry.decode())
            raw_attributes, raw_path = line.split("\"/\"", 2)
            attributes = raw_attributes.strip("() ")
            path = raw_path.strip("\" ")
            if "\\Spam" not in line and "\\Trash" not in attributes:
                names.append(path)

        return names

    def list_eids(self, mailbox: str) -> List[str]:
        self._ensure_selected_mailbox(mailbox)

        try:
            status, messages = self.mail_client.search(None, 'ALL')
        except imaplib.IMAP4.abort:
            self._connect(mailbox)
            status, messages = self.mail_client.search(None, 'ALL')
        except imaplib.IMAP4.error:
            return []
        except Exception as e:
            logger.error(f"[MailCache] {self.email}: {e}.")
            raise e

        email_ids = messages[0].split()

        return [str(x.decode()) for x in email_ids]

    def _fetch_raw(self, mailbox, eid: str) -> Optional[bytes]:
        self._ensure_selected_mailbox(mailbox)
        try:
            status, msg_data = self.mail_client.fetch(eid, "(RFC822)")
        except imaplib.IMAP4.abort:
            self._connect(mailbox)
            status, msg_data = self.mail_client.fetch(eid, "(RFC822)")
        except imaplib.IMAP4.error:
            return None
        except Exception as e:
            logger.error(f"[MailCache] {self.email}: {e}. EID: {eid}")
            raise e
        response = msg_data[0]
        if response is None:
            return None
        elif type(response) is bytes:
            return response
        else:
            # noinspection PyUnresolvedReferences
            return response[1]

    def get_msg_text_file(self, mailbox: str, eid: str) -> Optional[str]:
        email_cache_dir = os.path.join(self.mail_cache, from_posix_path(mailbox), eid)
        if not os.path.exists(email_cache_dir):
            os.makedirs(email_cache_dir, exist_ok=True)
        email_file_path = os.path.join(email_cache_dir, "msg.txt")

        if not os.path.exists(email_file_path):
            self._ensure_selected_mailbox(mailbox)
            raw_email = self._fetch_raw(mailbox, eid)
            if raw_email is None:
                return None
            save_email_text(raw_email, email_file_path)
        return email_file_path


class IMAPMailSource(DocSource):
    def __init__(self, host: str, port: int, email: str, pw: str,
                 name: str, cache_hashes: bool = True, skip_verify=False, cache_dir: str = DocSource.DEFAULT_CACHE_DIR):
        super().__init__("mail_imap", name, cache_hashes, cache_dir)
        self.mail_cache = MailCache(host, port, email, pw, skip_verify)

    def _list(self, pattern=None) -> List[Dict[str, Union[str, bool]]]:
        def list_items(mailboxes):
            items = []

            for mailbox in mailboxes:
                email_ids = self.mail_cache.list_eids(mailbox)
                items.append(
                    {"path": self.name + "/" + mailbox, "is_file": False, "is_dir": True}
                )
                items += [
                    {
                        "path": self.name + "/" + mailbox + "/" + x,
                        "is_file": True,
                        "is_dir": False,
                    }
                    for x in email_ids
                ]
            return items

        all_mailboxes = self.mail_cache.list_mailboxes()
        # easy special cases
        if pattern == self.name + "/*":
            return [{"path": self.name + "/" + x, "is_file": False, "is_dir": True} for x in
                    all_mailboxes if "/" not in x]
        if pattern == self.name + "/**":
            items = [{"path": self.name + "/" + x, "is_file": False, "is_dir": True} for x in all_mailboxes]
            items += list_items(all_mailboxes)
            return items
        # default if we cannot narrow the list => check everything
        mailboxes_to_check = all_mailboxes

        init = pattern.rsplit("/", 1)[0]
        if not DocSource._is_glob_pattern(init):
            # patterns like ABC/* ABC/DEF/**
            mailboxes_to_check = [mailbox for mailbox in all_mailboxes if (self.name + "/" + mailbox).startswith(init)]

        unfiltered = list_items(mailboxes_to_check)

        r_expr = re.compile(glob2regex(pattern, glob_star=True))

        return [item for item in unfiltered if r_expr.match(item["path"])]

    def get(self, path: str) -> Optional[DocumentFile]:
        init, eid = to_posix_path(path).rsplit("/", maxsplit=1)
        mailbox = init.split("/", maxsplit=1)[-1]
        email_file_path = self.mail_cache.get_msg_text_file(mailbox, eid)
        if email_file_path is None:
            return None
        last_modified = datetime.datetime.fromtimestamp(
            timestamp=os.stat(email_file_path).st_mtime,
            tz=datetime.UTC
        )
        return TextDocumentFile(self.name, self.mail_cache.mail_cache, email_file_path, last_modified=last_modified)
