import http.client
import asyncio
import json
import random
import string
import time
import base64
from datetime import datetime
from urllib.parse import unquote
from utils.headers import headers_set
from utils.queries import QUERY_USER, QUERY_LOGIN, MUTATION_GAME_PROCESS_TAPS_BATCH, QUERY_BOOSTER, QUERY_NEXT_BOSS
from utils.queries import QUERY_TASK_VERIF, QUERY_TASK_COMPLETED, QUERY_GET_TASK, QUERY_TASK_ID, QUERY_GAME_CONFIG

url = "https://api-gw-tg.memefi.club/graphql"
def load_proxies():
    with open('proxy.txt', 'r') as file:
        proxies = [line.strip() for line in file.readlines()]
    return proxies

proxies = load_proxies()

# HANDLE SEMUA ERROR TAROH DISINI BANG SAFE_POST
def safe_post(index,url, headers, json_payload):
    retries = 5
    timeout = 5  # Timeout in seconds for each connection attempt
    for attempt in range(retries):
        try:
            if proxies:
                proxy = proxies[index]
                print(str(url))
                print(str(proxy))
                if '@' in proxy:
                    user_pass, proxy_ip = proxy.split('@')
                    proxy_auth = base64.b64encode(user_pass.encode()).decode()
                else:
                    proxy_ip = proxy
                    proxy_auth = None

                conn = http.client.HTTPSConnection(proxy_ip, timeout=timeout)
                if proxy_auth:
                    conn.set_tunnel(url, 443, headers={"Proxy-Authorization": f"Basic {proxy_auth}"})
                else:
                    conn.set_tunnel(url, 443)
            else:
                conn = http.client.HTTPSConnection(url, timeout=timeout)
            
            payload = json.dumps(json_payload)
            conn.request("POST", "/graphql", payload, headers)
            res = conn.getresponse()
            response_data = res.read().decode("utf-8")
            if res.status == 200:
                return json.loads(response_data)  # Return the JSON response if successful
            else:
                print(f"❌ Failed with status {res.status}, Try again ")
        except (http.client.HTTPException, TimeoutError) as e:
            print(f"❌ Error: {e}, Try again ")
        if attempt < retries - 1:  # Jika ini bukan percobaan terakhir, tunggu sebelum mencoba lagi
            time.sleep(10)
        else:
            print("❌ Failed after several attempts. Restart...")
            return None
    return None

def generate_random_nonce(length=52):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Mendapatkan akses token
def fetch(account_line):
    with open('query_id.txt', 'r') as file:
        lines = file.readlines()
        raw_data = lines[account_line - 1].strip()

    tg_web_data = unquote(unquote(raw_data))
    query_id = tg_web_data.split('query_id=', maxsplit=1)[1].split('&user', maxsplit=1)[0]
    user_data = tg_web_data.split('user=', maxsplit=1)[1].split('&auth_date', maxsplit=1)[0]
    auth_date = tg_web_data.split('auth_date=', maxsplit=1)[1].split('&hash', maxsplit=1)[0]
    hash_ = tg_web_data.split('hash=', maxsplit=1)[1].split('&', maxsplit=1)[0]

    user_data_dict = json.loads(unquote(user_data))

    url = 'api-gw-tg.memefi.club'
    headers = headers_set.copy()  # Use headers from utils/headers.py
    data = {
        "operationName": "MutationTelegramUserLogin",
        "variables": {
            "webAppData": {
                "auth_date": int(auth_date),
                "hash": hash_,
                "query_id": query_id,
                "checkDataString": f"auth_date={auth_date}\nquery_id={query_id}\nuser={unquote(user_data)}",
                "user": {
                    "id": user_data_dict["id"],
                    "allows_write_to_pm": user_data_dict["allows_write_to_pm"],
                    "first_name": user_data_dict["first_name"],
                    "last_name": user_data_dict["last_name"],
                    "username": user_data_dict.get("username", "Username gak diset"),
                    "language_code": user_data_dict["language_code"],
                    "version": "7.2",
                    "platform": "ios",
                    "is_premium": user_data_dict.get("is_premium", False)
                }
            }
        },
        "query": "mutation MutationTelegramUserLogin($webAppData: TelegramWebAppDataInput!) {\n  telegramUserLogin(webAppData: $webAppData) {\n    access_token\n    __typename\n  }\n}"
    }

    conn = http.client.HTTPSConnection(url)
    payload = json.dumps(data)
    conn.request("POST", "/graphql", payload, headers)
    res = conn.getresponse()
    response_data = res.read().decode("utf-8")

    if res.status == 200:
        try:
            json_response = json.loads(response_data)
            if 'errors' in json_response:
                return None
            else:
                access_token = json_response['data']['telegramUserLogin']['access_token']
                return access_token
        except json.JSONDecodeError:
            print("Failed to decode JSON response")
            return None
    else:
        return None

# Cek akses token
def cek_user(index):
    access_token = fetch(index + 1)
    url = "api-gw-tg.memefi.club"

    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    headers['Authorization'] = f'Bearer {access_token}'

    json_payload = {
        "operationName": "QueryTelegramUserMe",
        "variables": {},
        "query": QUERY_USER
    }

    response = safe_post(index,url, headers, json_payload)
    if response and 'errors' not in response:
        user_data = response['data']['telegramUserMe']
        return user_data  # Mengembalikan hasil response
    else:
        print(f"❌ Failed status {response}")
        return None  # Mengembalikan None jika terjadi error

def activate_energy_recharge_booster(index, headers):
    access_token = fetch(index + 1)
    url = "api-gw-tg.memefi.club"

    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    headers['Authorization'] = f'Bearer {access_token}'

    recharge_booster_payload = {
        "operationName": "telegramGameActivateBooster",
        "variables": {"boosterType": "Recharge"},
        "query": QUERY_BOOSTER
    }

    response = safe_post(index,url, headers, recharge_booster_payload)
    if response and 'data' in response and response['data'] and 'telegramGameActivateBooster' in response['data']:
        new_energy = response['data']['telegramGameActivateBooster']['currentEnergy']
        print(f"\n🔋 Energy is charged. Current energy: {new_energy}")
    else:
        print("❌ Failed to activate Recharge Booster: Incomplete or missing data.")

def activate_booster(index, headers):
    access_token = fetch(index + 1)
    url = "api-gw-tg.memefi.club"
    print("\r🚀 Activating Turbo Boost ... ", end="", flush=True)

    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    headers['Authorization'] = f'Bearer {access_token}'

    recharge_booster_payload = {
        "operationName": "telegramGameActivateBooster",
        "variables": {"boosterType": "Turbo"},
        "query": QUERY_BOOSTER
    }

    response = safe_post(index,url, headers, recharge_booster_payload)
    if response and 'data' in response:
        current_health = response['data']['telegramGameActivateBooster']['currentBoss']['currentHealth']
        current_level = response['data']['telegramGameActivateBooster']['currentBoss']['level']
        if current_health == 0:
            print("\nThe boss has been defeated, set the next boss...")
            set_next_boss(index, headers)
        else:
            if god_mode == 'y':
                total_hit = 500000000
            else:
                total_hit = 500000
            tap_payload = {
                "operationName": "MutationGameProcessTapsBatch",
                "variables": {
                    "payload": {
                        "nonce": generate_random_nonce(),
                        "tapsCount": total_hit
                    }
                },
                "query": MUTATION_GAME_PROCESS_TAPS_BATCH
            }
            for _ in range(50):
                print("tab...")
                tap_result = submit_taps(index, tap_payload)
                if tap_result is not None:
                    if 'data' in tap_result and 'telegramGameProcessTapsBatch' in tap_result['data']:
                        tap_data = tap_result['data']['telegramGameProcessTapsBatch']
                        if tap_data['currentBoss']['currentHealth'] == 0:
                            print("\nThe boss has been defeated, set the next boss...")
                            set_next_boss(index, headers)
                            print(f"\rTapped ✅ Coin: {tap_data['coinsAmount']}, Monster ⚔️: {tap_data['currentBoss']['currentHealth']} - {tap_data['currentBoss']['maxHealth']}    ")
                else:
                    print(f"❌ Failed with status {tap_result}, Try again...")
    else:
        print(f"❌ Failed with status {response}, Try again...")

def submit_taps(index, json_payload):
    access_token = fetch(index + 1)
    url = "api-gw-tg.memefi.club"

    headers = headers_set.copy()
    headers['Authorization'] = f'Bearer {access_token}'

    response = safe_post(index,url, headers, json_payload)
    if response:
        return response  # Pastikan mengembalikan data yang sudah diurai
    else:
        print(f"❌ Failed with status {response}, Try again...")
        return None  # Mengembalikan None jika terjadi error

def set_next_boss(index, headers):
    access_token = fetch(index + 1)
    url = "api-gw-tg.memefi.club"

    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    headers['Authorization'] = f'Bearer {access_token}'
    boss_payload = {
        "operationName": "telegramGameSetNextBoss",
        "variables": {},
        "query": QUERY_NEXT_BOSS
    }

    response = safe_post(index,url, headers, boss_payload)
    if response and 'data' in response:
        print("✅ Successfully changing bosses.", flush=True)
    else:
        print("❌ Failed to change bosses.", flush=True)

# cek stat
def cek_stat(index, headers):
    access_token = fetch(index + 1)
    url = "api-gw-tg.memefi.club"

    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    headers['Authorization'] = f'Bearer {access_token}'

    json_payload = {
        "operationName": "QUERY_GAME_CONFIG",
        "variables": {},
        "query": QUERY_GAME_CONFIG
    }

    response = safe_post(index,url, headers, json_payload)
    if response and 'errors' not in response:
        user_data = response['data']['telegramGameGetConfig']
        return user_data
    else:
        print(f"❌ Fails with status {response}")
        return None  # Mengembalikan None jika terjadi error

def check_and_complete_tasks(index, headers):
    access_token = fetch(index + 1)
    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    headers['Authorization'] = f'Bearer {access_token}'
    task_list_payload = {
        "operationName": "GetTasksList",
        "variables": {"campaignId": "50ef967e-dd9b-4bd8-9a19-5d79d7925454"},
        "query": QUERY_GET_TASK
    }

    response = safe_post(index,url, headers, task_list_payload)
    if response and 'errors' not in response:
        tasks = response
    else:
        print(f"❌ Fails with status {response}")
        return False

    all_completed = all(task['status'] == 'Completed' for task in tasks['data']['campaignTasks'])
    if all_completed:
        print(f"\r[ Akun {index + 1} ] All tasks have been completed. ✅            ", flush=True)
        return True

    print(f"\n[ Akun {index + 1} ]\nList Task:\n")
    for task in tasks['data']['campaignTasks']:
        print(f"{task['name']} | {task['status']}")

        if task['name'] == "Follow telegram channel" and task['status'] == "Pending":
            print(f"⏩ Skipping task: {task['name']}")
            continue  # Skip task jika nama task adalah "Follow telegram channel" dan statusnya "Pending"

        if task['status'] == "Pending":
            print(f"\🔍 Viewing task: {task['name']}", end="", flush=True)

            view_task_payload = {"operationName": "GetTaskById", "variables": {"taskId": task['id']}, "query": "fragment FragmentCampaignTask on CampaignTaskOutput {\n  id\n  name\n  description\n  status\n  type\n  position\n  buttonText\n  coinsRewardAmount\n  link\n  userTaskId\n  isRequired\n  iconUrl\n  __typename\n}\n\nquery GetTaskById($taskId: String!) {\n  campaignTaskGetConfig(taskId: $taskId) {\n    ...FragmentCampaignTask\n    __typename\n  }\n}"}
            print(view_task_payload)
            view_response = safe_post(index,url, headers, view_task_payload)
            if 'errors' in view_response:
                print(f"\r❌ Failed to get task details: {task['name']}")
                print(view_response)
            else:
                task_details = view_response['data']['campaignTaskGetConfig']
                print(f"\r🔍 Detail Task: {task_details['name']}", end="", flush=True)

  

            print(f"\r🔍 Task verification: {task['name']}                                                                ", end="", flush=True)
            verify_task_payload = {
                "operationName": "CampaignTaskToVerification",
                "variables": {"userTaskId": task['userTaskId']},
                "query": QUERY_TASK_VERIF
            }
            verify_response = safe_post(index,url, headers, verify_task_payload)
            if 'errors' not in verify_response:
                print(f"\r✅ {task['name']} | Moved to Verification", flush=True)
            else:
                print(f"\r❌ {task['name']} | Failed to move to Verification", flush=True)
                print(verify_response)

         

    # Cek ulang task setelah memindahkan ke verification
    updated_tasks = safe_post(index,url, headers, task_list_payload)
    print("\nUpdated Task List After Verification:\n")
    for task in updated_tasks['data']['campaignTasks']:
        print(f"{task['name']} | {task['status']}")
        if task['status'] == "Verification":
            print(f"\r🔥 Complete tasks: {task['name']}", end="", flush=True)
            complete_task_payload = {
                "operationName": "CampaignTaskCompleted",
                "variables": {"userTaskId": task['userTaskId']},
                "query": QUERY_TASK_COMPLETED
            }
            complete_response = safe_post(index,url, headers, complete_task_payload)
            if 'errors' not in complete_response:
                print(f"\r✅ {task['name']} | Completed                         ", flush=True)
            else:
                print(f"\r❌ {task['name']} | Failed to complete            ", flush=True)

   

    return False

def main():
    print("Starting Memefi bot...")
    print("\r Get a list of valid accounts...", end="", flush=True)
  
    while True:
        with open('query_id.txt', 'r') as file:
            lines = file.readlines()

        # Kumpulkan informasi akun terlebih dahulu
        accounts = []
        for index, line in enumerate(lines):
            result = None
            try:
                result = cek_user(index)
            except Exception as e:
                print("check error..........")
            if result is not None:
                first_name = result.get('firstName', 'Unknown')
                last_name = result.get('lastName', 'Unknown')
                league = result.get('league', 'Unknown')
                accounts.append((index, result, first_name, last_name, league))
            else:
                print(f"❌ Account {index + 1}: Token is invalid or an error occurred")

        # Menampilkan daftar Account
        print("\rList Account:                                   ", flush=True)
        for index, _, first_name, last_name, league in accounts:
            print(f"✅ [ Account {first_name} {last_name} ] | League 🏆 {league}")

        # Setelah menampilkan semua akun, mulai memeriksa tugas
        for index, result, first_name, last_name, league in accounts:
            try:
                print(f"\r[ Account {index + 1} ] {first_name} {last_name} Check the task...", end="", flush=True)
                headers = {'Authorization': f'Bearer {result}'}
                if cek_task_enable == 'y':
                    check_and_complete_tasks(index, headers)
                else:
                    print(f"\r\n[ Account {index + 1} ] {first_name} {last_name} Cek task skipped\n", flush=True)
                stat_result = cek_stat(index, headers)
    
                if stat_result is not None:
                    user_data = stat_result
                    output = (
                        f"[ Account {index + 1} - {first_name} {last_name} ]\n"
                        f"Coin 🪙  {user_data['coinsAmount']:,} 🔋 {user_data['currentEnergy']} - {user_data['maxEnergy']}\n"
                        f"Level 🔫 {user_data['weaponLevel']} 🔋 {user_data['energyLimitLevel']} ⚡ {user_data['energyRechargeLevel']} 🤖 {user_data['tapBotLevel']}\n"
                        f"Boss 👾 {user_data['currentBoss']['level']} ❤️ {user_data['currentBoss']['currentHealth']} - {user_data['currentBoss']['maxHealth']}\n"
                        f"Free 🚀 {user_data['freeBoosts']['currentTurboAmount']} 🔋 {user_data['freeBoosts']['currentRefillEnergyAmount']}\n"
                    )
                    print(output, end="", flush=True)
                    level_bos = user_data['currentBoss']['level']
                    darah_bos = user_data['currentBoss']['currentHealth']
    
                    if darah_bos == 0:
                        print("\nThe boss has been defeated, set the next boss...", flush=True)
                        set_next_boss(index, headers)
                    print("\rTapping 👆", end="", flush=True)
    
                    energy_sekarang = user_data['currentEnergy']
                    energy_used = energy_sekarang - 100
                    damage = user_data['weaponLevel'] + 1
                    total_tap = energy_used // damage
    
                    if energy_sekarang < 0.25 * user_data['maxEnergy']:
                        if auto_booster == 'y':
                            if user_data['freeBoosts']['currentRefillEnergyAmount'] > 0:
                                print("\r🪫 Energy Depleted, activate Recharge Booster... \n", end="", flush=True)
                                activate_energy_recharge_booster(index, headers)
                                continue  # Lanjutkan tapping setelah recharge
                            else:
                                print("\r🪫 Energy Depleted, no boosters available. Moving on to the next account.\n", flush=True)
                                continue  # Beralih ke akun berikutnya
                        else:
                            print("\r🪫 Energy is out, auto booster disabled. Moving on to the next account.\n", flush=True)
                            continue  # Beralih ke akun berikutnya
    
                    tap_payload = {
                        "operationName": "MutationGameProcessTapsBatch",
                        "variables": {
                            "payload": {
                                "nonce": generate_random_nonce(),
                                "tapsCount": total_tap
                            }
                        },
                        "query": MUTATION_GAME_PROCESS_TAPS_BATCH
                    }
                    tap_result = submit_taps(index, tap_payload)
                    if tap_result is not None:
                        print(f"\rTapped ✅\n ")
                    else:
                        print(f"❌ Failed with status {tap_result}, try again...")
    
                    if turbo_booster == 'y':
                        if user_data['freeBoosts']['currentTurboAmount'] > 0:
                            activate_booster(index, headers)
            except Exception as e:
                print("error...........")
        print("=== [ ALL ACCOUNTS HAVE BEEN PROCESSED ] ===")
       
        wait_num =  random.randint(600, 2500)
        animate_energy_recharge(wait_num)

# Jalankan fungsi main() dan simpan hasilnya

def animate_energy_recharge(duration):
    frames = ["|", "/", "-", "\\"]
    end_time = time.time() + duration
    while time.time() < end_time:
        remaining_time = int(end_time - time.time())
        for frame in frames:
            print(f"\r🪫 Recharge energy {frame} - Tersisa {remaining_time} second         ", end="", flush=True)
            time.sleep(0.25)
    print("\r🔋 Energy charging complete.                            ", flush=True)

cek_task_enable = 'n'

# Automatically set boosters to 'y' without asking the user
auto_booster = 'y'
turbo_booster = 'y'
god_mode = 'y'

# Jalankan fungsi main() dan simpan hasilnya
main()
