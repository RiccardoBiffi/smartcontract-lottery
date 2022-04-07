from brownie import Contract, MockV3Aggregator, network, accounts, config
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
    # MockContract.LINK_TOKEN: LinkToken,
    MockContract.ETH_USD_PRICE_FEE: MockV3Aggregator,
    # MockContract.VRF_COORDINATOR: VRFCoordinatorV2Mock,
    # MockContract.ORACLE: MockOracle,
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
    Ottiene l'address del contract specificato.
    Se l'address è definito in brownie-config, lo prende da lì;
    altrimenti viene deployato un contratto mock e viene ritornato il suo address

    Args:
        contract_name (string): nome del contratto da ottenere
        tx_account (address): l'account che eventualmente deploya il mock

    Returns:
        brownie.network.contract.ProjectContract : l'ultima versione deployata del contratto
    """
    contract_type = contract_to_mock[contract_enum]
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        # il contratto esiste già nel fork della blockchain
        contract_address = config["networks"][network.show_active()][
            contract_enum.value
        ]
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
    else:
        contract = deploy_mock(contract_type)

    return contract


def deploy_mock(contract_type):
    # Restituisce il contratto richiesto
    # Controlla se è già deployato sulla network attiva, in caso lo deploya
    print(f"Active network: {network.show_active()}")

    if len(contract_type) == 0:
        print("Deploying Mocks...")
        MockV3Aggregator.deploy(DECIMALS, STARTING_PRICE, {"from": get_account()})
        print(f"Mock deployed")

    return contract_type[-1]
