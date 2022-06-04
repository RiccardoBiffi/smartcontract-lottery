// SPDX-License-Identifier: MIT

pragma solidity ^0.8.7;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";
import "@brownie-cl/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";
import "@brownie-cl/contracts/src/v0.8/interfaces/LinkTokenInterface.sol";
import "@chainlink/contracts/src/v0.8/interfaces/VRFCoordinatorV2Interface.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBaseV2.sol";

contract Lottery is VRFConsumerBaseV2, Ownable {
    enum LOTTERY_STATE {
        STARTED,
        ENDED,
        CALCULATING_WINNER
    }

    address payable[] public players;
    uint256 public usdEntryFee;
    LOTTERY_STATE public state;
    address public lastWinner;

    AggregatorV3Interface internal ethUsdPriceFeed;
    event RequestedRandomness(uint256 requestId);

    // Proprietà per utilizzare Chainlink VRF
    // Request
    VRFCoordinatorV2Interface COORDINATOR;
    LinkTokenInterface LINKTOKEN;
    uint64 subscriptionId; // contract che genera VRF usando LINK
    address vrfCoordinator; // address del coordinatore sulla blockchain
    address link; // address del sc LINK sulla blockchain
    bytes32 keyHash; // specifica il gas lane
    uint32 callbackGasLimit; // quanto gas dare al callback. Circa 20k / random-word
    uint16 requestConfirmations; // Numero di block confirm prima del callback
    uint32 numWords; // numero di random-word da ricevere

    // Response
    uint256 public randomWord;
    uint256 public requestId;

    constructor(
        address _priceFeedAddress,
        address _vrfCoordinator,
        address _link,
        uint64 _subscriptionId,
        bytes32 _keyhash,
        uint32 _callbackGasLimit,
        uint16 _requestConfirmations,
        uint32 _numWords
    ) VRFConsumerBaseV2(_vrfCoordinator) {
        usdEntryFee = 50 * 10**18;
        state = LOTTERY_STATE.ENDED;
        ethUsdPriceFeed = AggregatorV3Interface(_priceFeedAddress);
        subscriptionId = _subscriptionId;
        vrfCoordinator = _vrfCoordinator;
        link = _link;
        keyHash = _keyhash;
        callbackGasLimit = _callbackGasLimit;
        requestConfirmations = _requestConfirmations;
        numWords = _numWords;

        COORDINATOR = VRFCoordinatorV2Interface(vrfCoordinator);
    }

    function enter() public payable {
        uint256 entranceFee = getEntranceFee();
        require(
            state == LOTTERY_STATE.STARTED,
            "The lottery is not open at the moment"
        );
        require(
            msg.value >= entranceFee,
            string(
                abi.encodePacked(
                    "Pay at least 50$ worth of ETH (",
                    Strings.toString(entranceFee / 10**9),
                    " gwei) to enter!"
                )
            )
        ); // min 50$
        players.push(payable(msg.sender));
    }

    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , , ) = ethUsdPriceFeed.latestRoundData();

        // considdera l'uso di SafeMath per Solidity con versioni basse
        uint256 normalPrice = uint256(price) * 10**10; // price ha 8 decimali
        uint256 entranceFee = (usdEntryFee * 10**18) / normalPrice;

        return entranceFee;
    }

    function startLottery() public onlyOwner {
        require(
            state == LOTTERY_STATE.ENDED,
            "The lottery cannot be started at the moment"
        );
        state = LOTTERY_STATE.STARTED;
    }

    function endLottery() public onlyOwner {
        require(
            state == LOTTERY_STATE.STARTED,
            "The lottery cannot be ended at this moment"
        );

        state = LOTTERY_STATE.CALCULATING_WINNER;

        // Pseudorandom: numero che descrive la difficoltà del blocco
        // è tra le proprietà del blocco, non usare in PROD.
        // il numero ottenuto è imprevedibile ma...è facilmente ripetibile!
        // uint256(
        //     keccak256( // keccak256 è l'algoritmo di hashing
        //         abi.encodePacked( // pacchetto di numeri "random"
        //             nonce, // prevedibile (eg numero transazione)
        //             msg.sender, // prevedibile
        //             block.difficulty, // pubblico e manipolabile dai miners
        //             block.timestamp // prevedibile
        //         )
        //     )
        // ) % players.length;

        // True randomness con Chainlink VRF (verifiable randomness function)
        // Architettura request&recieve asincrona: request a Chainlink (aspetto una callback)
        requestId = COORDINATOR.requestRandomWords(
            keyHash,
            subscriptionId,
            requestConfirmations,
            callbackGasLimit,
            numWords
        );
        // gli eventi sono log sulla blockchain non accessibili agli smart contract
        // utili sia per debug che per testing
        emit RequestedRandomness(requestId);
    }

    // funzione di callback.
    // internal così può essere chiamata da ConsumerBaseV2
    // override perché il metodo fulfillRandomWords è virtual
    function fulfillRandomWords(
        uint256 _requestId,
        uint256[] memory _randomWords
    ) internal override {
        require(
            state == LOTTERY_STATE.CALCULATING_WINNER,
            "The lottery is not calculating the winner."
        );
        for (uint256 i = 0; i < _randomWords.length; i++) {
            require(_randomWords[i] > 0, "Not random number");
        }
        randomWord = _randomWords[0];
        uint256 winnerIndex = randomWord % players.length;
        players[winnerIndex].transfer(address(this).balance);

        state = LOTTERY_STATE.ENDED;
        lastWinner = players[winnerIndex];
        players = new address payable[](0);
    }
}
