import time
from brownie import Lottery, network, config
from scripts.utilities import MockContract, get_account, get_contract


def deploy_lottery():
    account = get_account(id="rick-testnet")
    # price_feed_address = get_price_feed_address(account)

    # Specificare sempre l'address nelle transazioni (ie accounts)
    # Pubblico il sorgente su Etherscan se non siamo in dev
    lottery = Lottery.deploy(
        get_contract(MockContract.ETH_USD_PRICE_FEE),  # price_feed_address
        {"from": account},
        publish_source=config["networks"][network.show_active()]["verify"],
    )
    print(f"Contratto deployato all'address {lottery.address} con successo!")
    time.sleep(1)
    return lottery


def main():
    deploy_lottery()
