from blockfrost import BlockFrostApi, ApiError, ApiUrls
import os
from dotenv import load_dotenv
import time

load_dotenv()

blockfrost_key = os.getenv("BLOCK_FROST_KEY")
mint_price = str(int(os.getenv("MINT_PRICE")) * 1000 * 1000)
policy_id = ""
asset_name = ""
full_hex_name = policy_id + asset_name

while True:
    with open("code/enable_exit.txt", 'r') as b:
        temp = b.read()
        exit_flag = temp.lower() == "true"
    b.close()

    if exit_flag:
        exit("Exit requested")

    with open("code/addresses_we_own_NFTs.txt", 'r') as r:
        old_addresses = r.read()
    r.close()

    if len(old_addresses) != 0:
        exit("You still haven't satisfied all the previous participants.")

    print("\nStill polling for incoming transactions..")
    time.sleep(35)

    with open("code/satisfied_till_block.txt", 'r') as h:
        start_block = h.read()
    h.close()

    with open("code/satisfied_till_index.txt", 'r') as n:
        tx_index = n.read()
    n.close()

    with open("keys/address.txt", 'r') as h:
        listener = h.read()
    h.close()

    api = BlockFrostApi(
        project_id=blockfrost_key,
        base_url=ApiUrls.mainnet.value,
    )

    try:
        saved_tx_ids = []
        tx_ids = api.address_transactions(
            listener, f"{start_block}:{tx_index}")

        for i in tx_ids:
            saved_tx_ids.append(i)

        print(len(saved_tx_ids))

        if saved_tx_ids:
            print(f"Searching for transactions at: {start_block}:{tx_index}")
            satisfied_till_block = saved_tx_ids[-1].block_height
            tx_index_last = saved_tx_ids[-1].tx_index
            print(f"I collected {len(saved_tx_ids)} transaction IDs till block {satisfied_till_block} and tx_index={tx_index_last}")

            addresses_that_sent_ADA = []
            for tx_id in saved_tx_ids:
                utxos = api.transaction_utxos(tx_id.tx_hash)

                for u in utxos.outputs:
                    if (
                        u.address == listener and
                        u.amount[0].quantity == mint_price and
                        len(u.amount) >= 2 and
                        u.amount[1].unit == full_hex_name and
                        u.amount[1].quantity == "10000000000"
                    ):
                        addresses_that_sent_ADA.append(utxos.inputs[0].address)

            print(addresses_that_sent_ADA)

            with open("code/satisfied_till_block.txt", 'w') as t:
                t.write(str(satisfied_till_block))
            t.close()

            with open("code/satisfied_till_index.txt", 'w') as m:
                m.write(str(tx_index_last + 1))
            m.close()

            with open("code/addresses_we_own_NFTs.txt", 'w') as q:
                for a in addresses_that_sent_ADA:
                    q.write(f'{str(a)}\n')
            q.close()

        else:
            print(f"No new transactions found after the block you specified {start_block}")

    except ApiError as e:
        print(e)
