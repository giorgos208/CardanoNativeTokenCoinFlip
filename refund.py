from blockfrost import ApiUrls, ApiError
from pycardano import *
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
vault_address = os.getenv('VAULT_ADDRESS')
blockfrost_key = os.getenv("BLOCK_FROST_KEY")

# Set network and context
network = Network.MAINNET
context = BlockFrostChainContext(blockfrost_key, base_url=ApiUrls.mainnet.value)

# Load keys and address
sk = PaymentSigningKey.load("keys/payment.skey")
vk = PaymentVerificationKey.from_signing_key(sk)
address = Address(vk.hash(), None, network)

# Read addresses from file
with open("code/addresses_we_own_NFTs.txt", 'r') as h:
    addresses = [line.strip() for line in h.readlines()]

# Exit if no address to mint
if not addresses:
    exit("No address to mint")

# Main loop for refunding
for address_to_refund in addresses:
    print(f"Left to refund: {len(addresses)}")
    print(f"Will refund on this address: {address_to_refund}")

    while True:
        try:
            chain_context = BlockFrostChainContext(
                project_id=blockfrost_key,
                base_url=ApiUrls.mainnet.value,
            )

            # Create a transaction builder
            builder = TransactionBuilder(context)
            builder.add_input_address(address)
            builder.add_output(TransactionOutput(
                Address.from_primitive(address_to_refund), Value.from_primitive([3_000_000])))

            signed_tx = builder.build_and_sign([sk], change_address=address)
            print(signed_tx.id)
            print("############### Submitting transaction ###############")
            context.submit_tx(signed_tx.to_cbor())
            break
        except ApiError as e:
            print(e)
            time.sleep(5)

    # Update addresses_we_own_NFTs.txt after successful transaction
    addresses.remove(address_to_refund)
    with open("code/addresses_we_own_NFTs.txt", 'w') as g:
        g.writelines([f"{line}\n" for line in addresses])
