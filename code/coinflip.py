from blockfrost import BlockFrostApi, ApiError, ApiUrls
import os
import time
import random
from dotenv import load_dotenv
from pycardano import *

# Load environment variables
load_dotenv()

# Initialize variables
blockfrost_key = os.getenv("BLOCK_FROST_KEY")
vault_address = os.getenv("VAULT_ADDRESS")
mint_price = str(int(os.getenv("MINT_PRICE")) * 1000 * 1000)
policy_id = "REDACTED_POLICY_ID"
asset_name = "REDACTED_ASSET_NAME"
full_hex_name = policy_id + asset_name
transaction_count = 0
dealer_address = os.getenv("dealer_address")
initial_pot = int(os.getenv("initial_pot"))


def SendWinnings(address_gabler, value_gambled, tx_hash_):
    global transaction_count
    network = Network.MAINNET
    sk = PaymentSigningKey.load("keys/payment.skey")
    vk = PaymentVerificationKey.from_signing_key(sk)
    address = Address(vk.hash(), None, network)

    while True:
        time.sleep(10)
        context = BlockFrostChainContext(blockfrost_key, base_url=ApiUrls.mainnet.value)
        builder = TransactionBuilder(context)
        builder.add_input_address(address)

        for k in range(len(address_gabler)):
            transaction_count += 1
            if int(value_gambled[k]) > 0:
                builder.add_output(
                    TransactionOutput(
                        Address.from_primitive(address_gabler[k]),
                        Value.from_primitive([
                            1500000,
                            {
                                bytes.fromhex(""): {
                                    b"": 1 * int(value_gambled[k])
                                }
                            }
                        ])
                    )
                )
            else:
                builder.add_output(
                    TransactionOutput(
                        Address.from_primitive(address_gabler[k]),
                        Value.from_primitive([1000000])
                    )
                )

        if transaction_count >= 5:
            print("FUNDS ARE SAFU.")
            transaction_count = 0
            builder.add_output(
                TransactionOutput(
                    Address.from_primitive(vault_address),
                    Value.from_primitive([2200000])
                )
            )

        signed_tx = builder.build_and_sign([sk], change_address=address)

        print("\n\nTrying to submit transaction..\n\n")
        try:
            context.submit_tx(signed_tx.to_cbor())
        except ApiError as e:
            time.sleep(5)
            print("Too fast, try again later")
            print(e)

        time.sleep(50)
        print("Trying to validate that my transaction had been submitted...")
        tries = 0
        is_submitted = False

        while True:
            tries += 1
            try:
                temp_api = BlockFrostApi(
                    project_id=blockfrost_key,
                    base_url=ApiUrls.mainnet.value
                )
                api_return = temp_api.transaction_utxos(str(signed_tx.id))
                is_submitted = True
                break
            except ApiError as e:
                print(e, "Error while checking for legitimacy of the SUBMITTED transaction hash. Waiting 30 seconds..", signed_tx.id)
                time.sleep(30)
                if tries >= 4:
                    print("\nTransaction FAILED.\n")
                    break

        if is_submitted:
            print("\n\nSuccessful submission!", signed_tx.id, "\n\n")
            with open("customers_log.txt", "a") as myfile:
                str_to_save = ""
                for l in range(len(tx_hash_)):
                    str_to_save += f"{tx_hash_[l]}|{int(value_gambled[l]) * 2}||"
                str_to_save += f",{signed_tx.id}\n"
                myfile.write(str_to_save)
            myfile.close()
            break
        else:
            time.sleep(10)
            print("Trying again..")
            transaction_count = 0
            SendWinnings(address_gabler, value_gambled, tx_hash_)


def hasPass(address_to_check):
    print("Will check this address:", address_to_check)
    
    try:
        temp_api = BlockFrostApi(
            project_id=blockfrost_key,  # or export environment variable BLOCKFROST_PROJECT_ID
            base_url=ApiUrls.mainnet.value,
        )
        
        api_return = temp_api.address(address_to_check)
        api_assets = api_return.amount
        flag = False
        
        # Define the policy ID for the NFT
        policy_id = "238b2d53fa9e2259c6377a9f0e9288edf3780739428e3aee67270c65"
        
        # Check if the address holds the NFT with the specified policy ID
        for i in range(len(api_assets)):
            if policy_id in api_assets[i].unit:
                print("Certified NFT holder")
                flag = True
                break
                
        if not flag:
            print("Not a Holder")
        
        return flag
    
    except ApiError as e:
        print(e, "Error while checking for NFT")
        exit()

def coinflip(array):
    to_send_addresses = []
    to_send_values = []
    to_send_hashes = []

    for i in range(len(array)):
        n = random.randint(0, 99)

        with open("code/coinflip_results/winnings.txt", 'r') as h:
            old_winnings = int(h.read())
        h.close()

        with open("code/coinflip_results/losings.txt", 'r') as q:
            old_losings = int(q.read())
        q.close()

        to_send_addresses.append(array[i]["gambler_address"])
        to_send_hashes.append(array[i]["tx_id"])

        if n < 47:
            print("Winner")
            old_winnings += int(array[i]["gambled_value"])
            to_send_values.append(array[i]["gambled_value"])

        else:
            print("Loser")
            old_losings += int(array[i]["gambled_value"])
            to_send_values.append("0")

        if len(to_send_addresses) >= 5:
            try:
                SendWinnings(to_send_addresses, to_send_values, to_send_hashes)
                to_send_addresses.clear()
                to_send_values.clear()
                to_send_hashes.clear()
            except Exception as e:
                print(f"Couldn't send ITEMS! {e}")

    if len(to_send_addresses) > 0:
        try:
            SendWinnings(to_send_addresses, to_send_values, to_send_hashes)
        except Exception as e:
            print(f"Couldn't send ITEMS2! {e}")

    with open("code/coinflip_results/losings.txt", 'w') as m:
        m.write(str(old_losings))
    m.close()

    with open("code/coinflip_results/winnings.txt", 'w') as n:
        n.write(str(old_winnings))
    n.close()

def dealer_winnings(number_flag):
    print("Withdrawal of profits attempted!")
    
    try:
        temp_api = BlockFrostApi(
            project_id=blockfrost_key,
            base_url=ApiUrls.mainnet.value
        )
        
        api_return = temp_api.address(listener)
        api_assets = api_return.amount
        flag = False
        policy_id = ""
        
        for i in range(len(api_assets)):
            if policy_id in api_assets[i].unit:
                print(f"Current Holdings: {api_assets[i].quantity}")
                
                if number_flag == 0:
                    win_value = int(api_assets[i].quantity) - initial_pot
                elif number_flag == 1:
                    win_value = int(api_assets[i].quantity)
                
                if win_value > 0:
                    print(f"Can claim: {win_value}")
                    flag = True
                    break
        
        print(f"Winnings: {win_value}")
        
        if not flag:
            print("Can't claim. You are losing as a dealer.")
        else:
            network = Network.MAINNET
            sk = PaymentSigningKey.load("keys/payment.skey")
            vk = PaymentVerificationKey.from_signing_key(sk)
            address = Address(vk.hash(), None, network)
            
            while True:
                time.sleep(50)
                context = BlockFrostChainContext(blockfrost_key, base_url=ApiUrls.mainnet.value)
                builder = TransactionBuilder(context)
                builder.add_input_address(address)
                builder.add_output(
                    TransactionOutput(
                        Address.from_primitive(dealer_address),
                        Value.from_primitive(
                            [
                                1500000,
                                {
                                    bytes.fromhex(policy_id): {
                                        b"": win_value * 1000 * 1000
                                    }
                                },
                            ]
                        )
                    )
                )
                
                signed_tx = builder.build_and_sign([sk], change_address=address)
                print("\nTrying to submit transaction...\n")
                
                try:
                    context.submit_tx(signed_tx.to_cbor())
                except ApiError as e:
                    time.sleep(5)
                    print("Too fast, try again later")
                    print(e)
                
                print(f"\nSuccesful submission! {signed_tx.id}\n")
                break
    
    except ApiError as e:
        print(f"{e} Error while checking for NFT")
        exit()


while True:
    # Check for exit flag
    with open("code/enable_exit.txt", 'r') as b:
        temp = b.read()
        exit_flag = temp.lower() == "true"
    b.close()

    if exit_flag:
        exit("Exit requested")

    # Check for old addresses
    with open("code/addresses_we_own_NFTs.txt", 'r') as r:
        old_addresses = r.read()
    r.close()

    if len(old_addresses) != 0:
        exit("You still haven't satisfied all the previous minters.")

    print("\nStill polling for incoming transactions..")
    time.sleep(35)

    # Reading from files
    with open("code/satisfied_till_block.txt", 'r') as h:
        start_block = h.read()
    h.close()

    with open("code/satisfied_till_index.txt", 'r') as n:
        tx_index = n.read()
    n.close()

    with open("keys/address.txt", 'r') as h:
        listener = h.read()
    h.close()

    # Initialize BlockFrostApi
    api = BlockFrostApi(
        project_id=blockfrost_key,
        base_url=ApiUrls.mainnet.value
    )

    try:
        saved_tx_ids = []
        tx_ids = api.address_transactions(listener, f"{start_block}:{tx_index}")

        for i in tx_ids:
            saved_tx_ids.append(i)

        # Business logic
        if len(saved_tx_ids) != 0:
            print(f"Searching for transactions at: {start_block}:{tx_index}")
            satisfied_till_block = saved_tx_ids[-1].block_height
            tx_index_last = saved_tx_ids[-1].tx_index

            print(f"I collected {len(saved_tx_ids)} transactions IDs till block {satisfied_till_block} and tx_index={tx_index_last}")
            addresses_that_sent_ADA = []

            for j in range(len(saved_tx_ids)):
                utxos = api.transaction_utxos(saved_tx_ids[j].tx_hash)

                for u in utxos.outputs:
                    #print(len(u.amount), u.amount)
                    if (u.address == listener and u.amount[0].quantity == mint_price and len(u.amount) >= 2 and u.amount[1].unit == full_hex_name):
                        
                        if (hasPass(utxos.inputs[0].address) and (int(u.amount[1].quantity)/1000000) >= 100 and (int(u.amount[1].quantity)/1000000) <= 1000): #999 10000
                            gambler = {
                                "gambled_value": str(int(int(u.amount[1].quantity)/1000000)),
                                "gambler_address": utxos.inputs[0].address,
                                "tx_id": saved_tx_ids[j].tx_hash
                            }
                            addresses_that_sent_ADA.append(gambler)
                    elif (u.address == listener and u.amount[0].quantity == mint_price and utxos.inputs[0].address == dealer_address):
                        dealer_winnings(0)
                    elif (u.address == listener and u.amount[0].quantity == "3000000" and utxos.inputs[0].address == dealer_address):
                        dealer_winnings(1)

            # Write to files
            with open("code/satisfied_till_block.txt", 'w') as t:
                t.write(str(satisfied_till_block))
            t.close()

            with open("code/satisfied_till_index.txt", 'w') as m:
                m.write(str(tx_index_last + 1))
            m.close()

            with open("code/addresses_we_own_NFTs.txt", 'w') as q:
                for a in addresses_that_sent_ADA:
                    q.write(f"{str(a)}\n")
            q.close()

        else:
            print(f"No new transactions found after the block you specified {start_block}")

    except ApiError as e:
        print(e)
