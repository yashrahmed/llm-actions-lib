import re
import boto3
from flask import Flask
from playwright.sync_api import sync_playwright



def get_secure_parameter(parameter_name="/my-address"):
    """
    Retrieve a SecureString parameter from AWS Systems Manager Parameter Store.

    Args:
        parameter_name (str): The name of the parameter to retrieve.

    Returns:
        str: The decrypted value of the parameter.

    Raises:
        Exception: If the parameter retrieval fails.
    """
    try:
        # Initialize the SSM client
        # Retrieve the parameter value
        ssm_client = boto3.client('ssm')
        response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
        # Return the parameter value
        return response['Parameter']['Value']
    
    except Exception as e:
        print(f"Failed to retrieve parameter '{parameter_name}': {str(e)}")
        return None


def scrape_groot_website(address) -> None:
    with sync_playwright() as playwright:
        # Launch browser in non-headless mode
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Navigate to the page
        page.goto("https://www.groot.com/groot-aurora")

        # Interact with elements
        page.get_by_label("Please type your home address:").click()
        page.get_by_label("Please type your home address:").fill(address)
        page.get_by_role("link", name="Search").click()
        page.get_by_label("Close the modal labeled: \"").click()

        # Interact with iframe content
        frame = page.locator("iframe[name=\"recollect\"]")
        frame.wait_for(timeout=1000)
        next_event_notice_heading = frame.content_frame.get_by_role("heading", name="Next Event")
        next_event_notice_heading.wait_for(timeout=1000)
        
        next_event_notice_details = next_event_notice_heading.locator('xpath=../*[position() > 1]/*').all()
        all_content = []
        for detail in next_event_notice_details:
            detail.wait_for(timeout=1000)
            text_content = re.sub(r'$[\s]+', '', detail.text_content(), flags=re.MULTILINE)
            all_content.append(f"<tr><td>{text_content}</td></tr>")
        html_formatted_content = '\n'.join(all_content) if len(all_content) else "<tr><td>No Information Available!</td></tr>"
        result = f"""
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Next trash collection day</title>
            </head>
            <body>
            <p>Next trash collection day | GROOT Aurora</p>
            <table>
            <tbody>
                {html_formatted_content}
            </tbody>
            </table>
            </body>
        </html>
        """
        # time.sleep(10)
        # Clean up
        context.close()
        browser.close()
        return result


app = Flask(__name__)

@app.route('/')
def about():
    return "LLM Actions Library"

@app.route('/get-next-collection-day')
def get_next_collections():
    address = get_secure_parameter()
    if not address:
        return "Failed to get info; There was a problem determining the correct location."
    return scrape_groot_website(address)

if __name__ == "__main__":
    
    app.run()