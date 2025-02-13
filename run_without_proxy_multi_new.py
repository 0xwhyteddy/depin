import asyncio
import time
import uuid
import cloudscraper
from loguru import logger
from fake_useragent import UserAgent

# Constants
PING_INTERVAL = 60
RETRIES = 60
BATCH_SIZE = 15  # Ukuran batch yang akan diproses per waktu

DOMAIN_API = {
    "SESSION": "http://api.nodepay.ai/api/auth/session",
    "PING": "http://nw.nodepay.ai/api/network/ping"
}

CONNECTION_STATES = {
    "CONNECTED": 1,
    "DISCONNECTED": 2,
    "NONE_CONNECTION": 3
}

status_connect = CONNECTION_STATES["NONE_CONNECTION"]
browser_id = None
account_info = {}
last_ping_time = {}  # Store ping times for each token

def uuidv4():
    return str(uuid.uuid4())
    
def valid_resp(resp):
    if not resp or "code" not in resp or resp["code"] < 0:
        raise ValueError("Invalid response")
    return resp

async def render_profile_info(token):
    global browser_id, account_info

    try:
        np_session_info = load_session_info()

        if not np_session_info:
            # Generate new browser_id
            browser_id = uuidv4()
            response = await call_api(DOMAIN_API["SESSION"], {}, token)
            valid_resp(response)
            account_info = response["data"]
            if account_info.get("uid"):
                save_session_info(account_info)
                await start_ping(token)  # Start pinging in background
            else:
                handle_logout()
        else:
            account_info = np_session_info
            await start_ping(token)  # Start pinging in background
    except Exception as e:
        logger.error(f"Error in render_profile_info: {e}")
        error_message = str(e)
        if any(phrase in error_message for phrase in [
            "sent 1011 (internal error) keepalive ping timeout; no close frame received",
            "500 Internal Server Error"
        ]):
            logger.info(f"Encountered an error, retrying...")
            return None
        else:
            logger.error(f"Connection error: {e}")
            return None

async def call_api(url, data, token):
    user_agent = UserAgent(os=['windows', 'macos', 'linux'], browsers='chrome')
    random_user_agent = user_agent.random
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": random_user_agent,
        "Content-Type": "application/json",
        "Origin": "chrome-extension://lgmpfmgeabnnlemejacfljbmonaomfmm",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        scraper = cloudscraper.create_scraper()

        response = scraper.post(url, json=data, headers=headers, timeout=30)

        response.raise_for_status()
        return valid_resp(response.json())
    except Exception as e:
        logger.error(f"Error during API call: {e}")
        raise ValueError(f"Failed API call to {url}")

async def start_ping(token):
    try:
        logger.info(f"Started pinging for token {token}")
        # Create a separate task for the ping process so it can run in background
        ping_task = asyncio.create_task(ping(token))
        await ping_task
    except asyncio.CancelledError:
        logger.info(f"Ping task was cancelled")
    except Exception as e:
        logger.error(f"Error in start_ping: {e}")
        
async def ping(token):
    global last_ping_time, RETRIES, status_connect

    current_time = time.time()

    # Check if the token has a separate last ping time and if enough time has passed
    if token in last_ping_time and (current_time - last_ping_time[token]) < PING_INTERVAL:
        logger.info(f"Skipping ping for token {token}, not enough time elapsed")
        return

    last_ping_time[token] = current_time  # Update the last ping time for this token

    try:
        data = {
            "id": account_info.get("uid"),
            "browser_id": browser_id,  
            "timestamp": int(time.time()),
            "version": "2.2.7"
        }

        response = await call_api(DOMAIN_API["PING"], data, token)
        if response["code"] == 0:
            logger.info(f"Ping successful for token {token}: {response}")
            RETRIES = 0
            status_connect = CONNECTION_STATES["CONNECTED"]
        else:
            handle_ping_fail(response)
    except Exception as e:
        logger.error(f"Ping failed for token {token}: {e}")
        handle_ping_fail(None)

def handle_ping_fail(response):
    global RETRIES, status_connect

    RETRIES += 1
    if response and response.get("code") == 403:
        handle_logout()
    elif RETRIES < 2:
        status_connect = CONNECTION_STATES["DISCONNECTED"]
    else:
        status_connect = CONNECTION_STATES["DISCONNECTED"]

def handle_logout():
    global status_connect, account_info

    status_connect = CONNECTION_STATES["NONE_CONNECTION"]
    account_info = {}
    logger.info(f"Logged out and cleared session info")

def save_session_info(data):
    data_to_save = {
        "uid": data.get("uid"),
        "browser_id": browser_id  
    }
    pass

def load_session_info():
    return {}  # Placeholder for loading session info

async def run_with_token(token):
    await render_profile_info(token)

def chunkify(input_list, chunk_size):
    start = 0
    while start < len(input_list):
        yield input_list[start:start + chunk_size]
        start += chunk_size

async def process_batch(tokens_batch, batch_number, total_batches):
    tasks = []
    logger.info(f"Processing batch {batch_number} of {total_batches}, containing {len(tokens_batch)} tokens")
    await asyncio.sleep(10)

    for token in tokens_batch:
        tasks.append(run_with_token(token))
    
    # Process the batch concurrently
    await asyncio.gather(*tasks)
    logger.info(f"Finished processing batch {batch_number}")  # Log batch finished

async def main():
    print("\nStarting multi-token processing without proxies...")
    
    while True:  # Loop to keep processing batches continuously
        try:
            with open('token_list.txt', 'r') as file:
                tokens = file.read().splitlines()
        except Exception as e:
            logger.error(f"Error reading token list: {e}")
            return

        if not tokens:
            print("No tokens found. Exiting.")
            return

        total_batches = (len(tokens) // BATCH_SIZE) + (1 if len(tokens) % BATCH_SIZE > 0 else 0)

        logger.info(f"Total tokens: {len(tokens)}")
        logger.info(f"Total batches: {total_batches}")

        for i, batch in enumerate(chunkify(tokens, BATCH_SIZE)):
            batch_number = i + 1
            logger.info(f"Starting batch {batch_number} of {total_batches}, containing {len(batch)} tokens")
            await process_batch(batch, batch_number, total_batches)
            logger.info(f"Finished processing batch {batch_number}")
            await asyncio.sleep(2)
        logger.info("Restarting batch process after completion...")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Program terminated by user.")
