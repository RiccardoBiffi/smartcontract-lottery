import time
from brownie import Lottery, network, config
from scripts.utilities import MockContract, get_account, get_contract


CALLBACK_GAS_LIMIT = 100000
REQUEST_CONFIRMATIONS = 3
NUM_WORDS = 1


def deploy_lottery():
    account = get_account(id="rick-testnet")
    # price_feed_address = get_price_feed_address(account)

    # Specificare sempre l'address nelle transazioni (ie accounts)
    # Pubblico il sorgente su Etherscan se non siamo in dev
    lottery = Lottery.deploy(
        get_contract(MockContract.ETH_USD_PRICE_FEE).address,  # price_feed_address
        get_contract(MockContract.VRF_COORDINATOR).address,  # VRF coordinator
        get_contract(MockContract.LINK_TOKEN).address,  # LINK contract
        config["subscriptions"]["chainlink"],
        config["networks"][network.show_active()]["keyhash"],
        CALLBACK_GAS_LIMIT,
        REQUEST_CONFIRMATIONS,
        NUM_WORDS,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    time.sleep(1)
    print(f"Contratto Lottery deployato all'address {lottery.address} con successo!")
    return lottery


def main():
    deploy_lottery()
