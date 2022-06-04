import time
from brownie import Lottery, accounts, config, network
import pytest
from web3 import Web3
from scripts.deploy_lottery import deploy_lottery

from scripts.utilities import LOCAL_BLOCKCHAIN_ENVIRONMENTS, get_account

# integration test per le interazioni tra funzioni del contract, in testnet


def test_can_pick_winner():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee() + 1000})
    lottery.enter({"from": account, "value": lottery.getEntranceFee() + 1000})
    lottery.enter({"from": account, "value": lottery.getEntranceFee() + 1000})
    lottery.endLottery({"from": account})

    # aspetta che chainlink chiami la mia callback
    time.sleep(30)

    assert lottery.lastWinner == account
    assert lottery.balance() == 0
    assert lottery.state == 0
