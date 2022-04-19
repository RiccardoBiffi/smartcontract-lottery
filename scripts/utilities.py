from brownie import (
    Contract,
    network,
    accounts,
    config,
)
from brownie import MockV3Aggregator, VRFCoordinatorV2Mock, LinkToken, MockOracle
from enum import Enum

FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork", "mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]
DECIMALS = 8
STARTING_PRICE = 2000 * 10**8


class MockContract(Enum):
    LINK_TOKEN = "link_token"
    ETH_USD_PRICE_FEE = "eth_usd_price_feed"
    VRF_COORDINATOR = "vrf_coordinator"
    ORACLE = "oracle"


contract_to_mock = {
    MockContract.LINK_TOKEN: LinkToken,
    MockContract.ETH_USD_PRICE_FEE: MockV3Aggregator,
    MockContract.VRF_COORDINATOR: VRFCoordinatorV2Mock,
    MockContract.ORACLE: MockOracle,
}


def get_account(index=None, id=None):
    if index:
        return accounts[index]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        return accounts[0]  # primo account offerto da Ganache
    if id:
        return accounts.load(id)

    # siamo in mainnet
    return accounts.add(config["wallets"]["from_key"])


def get_contract(contract_enum):
    """
    Ottiene il contract specificato.
    Se la blockchain è un fork o esterna, lo prende leggendo l'address da brownie-config;
    altrimenti, se siamo su una blockchain locale, viene deployato un mock e restituito.

    Args:
        contract_name (string): nome del contratto da ottenere

    Returns:
        brownie.network.contract.ProjectContract : l'ultima versione deployata del contratto,
        che può essere un mock o un contratto "reale" già presente sul network
    """
    contract_type = contract_to_mock[contract_enum]

    if is_local_blockchain():
        if len(contract_type) == 0:  # contratto mai deployato
            contract = deploy_mock(contract_enum)
        contract = contract_type[-1]  # prendo l'ultimo contratto deployato

    else:
        # il contratto esiste già nel fork della blockchain
        contract_address = config["networks"][network.show_active()][
            contract_enum.value
        ]
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )

    return contract


def is_local_blockchain():
    return network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS


LINK_BASE_FEE = 1 * 10**8 * 10**9
LINK_GAS_PRICE = 1 * 10**9


def deploy_mock(contract_enum):
    """
    Deploya il contratto in input.
    """
    print(f"Deploying mock {contract_enum.value} to network: {network.show_active()}")
    if contract_enum == MockContract.LINK_TOKEN:
        LinkToken.deploy({"from": get_account()})
    elif contract_enum == MockContract.ETH_USD_PRICE_FEE:
        MockV3Aggregator.deploy(DECIMALS, STARTING_PRICE, {"from": get_account()})
    elif contract_enum == MockContract.VRF_COORDINATOR:
        VRFCoordinatorV2Mock.deploy(
            LINK_BASE_FEE, LINK_GAS_PRICE, {"from": get_account()}
        )
    print(f"Mock deployed!")
