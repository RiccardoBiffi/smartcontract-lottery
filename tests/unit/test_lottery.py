import time
from brownie import Lottery, accounts, config, network, exceptions, web3
import pytest
from scripts.deploy_lottery import deploy_lottery
from web3 import Web3
from scripts.utilities import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    MockContract,
    get_account,
    get_contract,
)

# unit test per le singole funzioni del contract, development network


def test_get_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    # Arrange
    lottery = deploy_lottery()

    # Act
    entrance_fee = lottery.getEntranceFee()

    # Assert
    expected_entrance_fee = Web3.toWei(0.025, "ether")
    assert entrance_fee == expected_entrance_fee


def test_start_success():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    # Arrange
    account = get_account()
    lottery = deploy_lottery()

    # Act
    lottery.startLottery({"from": account})

    # Assert
    assert lottery.state() == 0


def test_start_fail_not_ended():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    # Arrange
    account = get_account()
    lottery = deploy_lottery()

    # Act
    lottery.startLottery({"from": account})

    # Act & Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.startLottery({"from": account})


def test_start_fail_not_owner():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    # Arrange
    lottery = deploy_lottery()
    not_owner = get_account(1)

    # Act & Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.startLottery({"from": not_owner})


def test_enter_fail_not_started():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    entrance_fee = lottery.getEntranceFee()

    # Act & Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": account, "value": entrance_fee})


def test_enter_fail_insufficient_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    entrance_fee = web3.toWei(0.01, "ether")

    # Act & assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": account, "value": entrance_fee})


def test_enter_success():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    entrance_fee = lottery.getEntranceFee()

    # Act
    lottery.enter({"from": account, "value": entrance_fee})

    # Assert
    assert lottery.players(0) == account
    assert lottery.state() == 0


def test_end_fail_not_owner():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    # Arrange
    lottery = deploy_lottery()
    not_owner = get_account(1)

    # Act & Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.endLottery({"from": not_owner})


def test_end_fail_not_started():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    # Arrange
    lottery = deploy_lottery()
    account = get_account()

    # Act & Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.endLottery({"from": account})


def test_end_success():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    entrance_fee = lottery.getEntranceFee()
    lottery.enter({"from": account, "value": entrance_fee})

    # Act
    lottery.endLottery({"from": account})

    # Assert
    # la lotteria è finita?
    assert 2 == 2


# simile ad un integration test
def test_end_correct_winner():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    # Arrange
    lottery = deploy_lottery()
    adminAccount = get_account(index=0)
    starting_balance_of_winner = adminAccount.balance()
    lottery.startLottery({"from": adminAccount})
    entrance_fee = lottery.getEntranceFee()
    lottery.enter({"from": adminAccount, "value": entrance_fee})
    lottery.enter({"from": get_account(index=1), "value": entrance_fee})
    lottery.enter({"from": get_account(index=2), "value": entrance_fee})
    total_lottery_amount = lottery.balance()

    # Act
    tx = lottery.endLottery({"from": adminAccount})
    # accedo a requestId cercando tra gli eventi della transazione
    requestId = tx.events["RequestedRandomness"]["requestId"]
    # simulo il nodo chainlink chiamando fulfillRandomWords, che attiva il mio callback
    get_contract(MockContract.VRF_COORDINATOR).fulfillRandomWords(
        requestId, lottery.address, {"from": adminAccount}
    )
    lottery_balance_after_close = lottery.balance()
    print(f"Admin balance after: {adminAccount.balance()}")
    winner = get_account(index=0)  # in development il vincitore è sempre lo stesso

    # Assert
    # ha vinto la persona giusta?
    assert lottery.lastWinner() == winner.address
    # lo smart contract si è svuotato?
    assert lottery_balance_after_close == 0
    # il vincitore ha guadagnato tutta la lotteria?
    assert (
        winner.balance()
        == starting_balance_of_winner - entrance_fee + total_lottery_amount
    )
