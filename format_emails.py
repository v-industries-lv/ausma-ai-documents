import os
import shutil
import json
from utils import compute_folder_hash

def main():
    emails_path = "emails"
    if not os.path.exists(emails_path):
        exit("Missing emails folder!")

    addresses = os.listdir(emails_path)

    for address in addresses:
        address_path = os.path.join(emails_path, address)
        emails = os.listdir(address_path)
        emails.remove("attachments")

        processed_path = os.path.join("processed", address)
        os.makedirs(processed_path, exist_ok=True)
        with open(os.path.join(processed_path, "metadata.json"), "w") as fh:
            json.dump(
                {
                    "type": "email",
                    "conversions": [
                        {
                            "conversion": "raw",
                            "model": None,
                            "output_folder": "raw",
                            "hash": compute_folder_hash(address_path),
                        }
                    ],
                    "email": address
                },
                fh,
                indent=2
            )
        output_path = os.path.join("processed", address, "raw")

        os.makedirs(output_path, exist_ok=True)
        for email in emails:
            email_path = os.path.join(address_path, email)
            text_output_path = os.path.join(output_path, email)
            shutil.copy2(email_path, text_output_path)


if __name__ == "__main__":
    main()