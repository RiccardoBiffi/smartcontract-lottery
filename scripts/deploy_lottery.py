from sqlite3 import Time
import time
from brownie import Lottery, accounts, network, config
from scripts.utilities import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    MockContract,
    get_account,
    get_contract,
    get_and_fund_subscription,
)


CALLBACK_GAS_LIMIT = 100000
REQUEST_CONFIRMATIONS = 3
NUM_WORDS = 1
LINK_FUND_AMOUNT = 5 * 10**8 * 10**9


def deploy_lottery():
    account = get_account(id="rick-testnet")
    vrf_coordinator = get_contract(MockContract.VRF_COORDINATOR)
    sub_id = get_and_fund_subscription()
    lottery = Lottery.deploy(
        get_contract(MockContract.ETH_USD_PRICE_FEE).address,  # price feed contract
        vrf_coordinator.address,  # VRF coordinator contract
        get_contract(MockContract.LINK_TOKEN).address,  # LINK contract
        sub_id,
        config["networks"][network.show_active()]["keyhash"],
        CALLBACK_GAS_LIMIT,
        REQUEST_CONFIRMATIONS,
        NUM_WORDS,
        # Specificare sempre l'address nelle transazioni (ie accounts)
        {"from": account},
        # Pubblico il sorgente su Etherscan se non siamo in dev
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    print(f"Contratto Lottery deployato all'address {lottery.address} con successo!\n")

    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        # devo aggiungere il contract come consumer
        print("Aggiungo lottery come consumer della sottoscrizione")
        vrf_coordinator.addConsumer.transact(
            sub_id,
            lottery.address,
            {"from": account},
        )

    return lottery


def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    lottery.startLottery({"from": account})
    print("The lottery has started!\n")


def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    entrance_fee = lottery.getEntranceFee() + 1 * 10**8
    lottery.enter({"from": account, "value": entrance_fee})
    print(f"{account.address} entered the lottery with {entrance_fee / 10**18} ETH!\n")


def end_lottery():
    account = get_account()
    lottery = Lottery[-1]

    tx = lottery.endLottery({"from": account, "gasPrice": 100000000000000000})

    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        # simulo il nodo chainlink chiamando fulfillRandomWords, che attiva il mio callback
        requestId = tx.events["RequestedRandomness"]["requestId"]
        get_contract(MockContract.VRF_COORDINATOR).fulfillRandomWords(
            requestId, lottery.address, {"from": account}
        )
    else:
        # attendo che il network chiami la mia callback
        time.sleep(120)

    print("The lottery has ended!\n")
    print(f"And the winner is...{lottery.lastWinner()}!!!\n")


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()

    time.sleep(1)  # per dare tempo all'ultima transazione di completarsi
