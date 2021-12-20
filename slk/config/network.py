from __future__ import annotations

from typing import List, Optional

from xrpl import CryptoAlgorithm
from xrpl.core.addresscodec import encode_account_public_key, encode_node_public_key
from xrpl.core.keypairs import derive_keypair, generate_seed
from xrpl.wallet import Wallet

from slk.config.helper_classes import Keypair, Ports


class Network:
    def __init__(self: Network, num_nodes: int, ports: List[Ports]) -> None:
        self.url = "127.0.0.1"
        self.num_nodes = num_nodes
        self.ports = ports


class StandaloneNetwork(Network):
    def __init__(self: StandaloneNetwork, num_nodes: int, start_cfg_index: int) -> None:
        ports = [Ports.generate(start_cfg_index + i) for i in range(num_nodes)]
        super().__init__(num_nodes, ports)
        self.validator_keypairs = self._generate_node_keypairs()

    def _generate_node_keypairs(self: StandaloneNetwork) -> List[Keypair]:
        """generate keypairs suitable for validator keys"""
        result = []
        for i in range(self.num_nodes):
            seed = generate_seed(None, CryptoAlgorithm.SECP256K1)
            pub_key, priv_key = derive_keypair(seed, True)
            result.append(
                Keypair(
                    public_key=encode_node_public_key(bytes.fromhex(pub_key)),
                    secret_key=seed,
                    account_id=None,
                )
            )
        return result


class ExternalNetwork(Network):
    def __init__(self: ExternalNetwork, url: str, ws_port: int) -> None:
        ports = [Ports(None, None, ws_port, None)]
        super().__init__(1, ports)
        self.url = url


class SidechainNetwork(StandaloneNetwork):
    def __init__(
        self: SidechainNetwork,
        num_federators: int,
        start_cfg_index: int,
        num_nodes: Optional[int] = None,
        main_door_seed: Optional[str] = None,
    ) -> None:
        super().__init__(num_nodes or num_federators, start_cfg_index)
        self.num_federators = num_federators
        self.federator_keypairs = self._generate_federator_keypairs()
        # TODO: main_account needs to be user-defined for external networks
        if main_door_seed is None:
            self.main_account = Wallet.create(CryptoAlgorithm.SECP256K1)
        else:
            self.main_account = Wallet(main_door_seed, 0)

    def _generate_federator_keypairs(self: SidechainNetwork) -> List[Keypair]:
        """generate keypairs suitable for federator keys"""
        result = []
        for i in range(self.num_federators):
            wallet = Wallet.create(crypto_algorithm=CryptoAlgorithm.ED25519)
            result.append(
                Keypair(
                    public_key=encode_account_public_key(
                        bytes.fromhex(wallet.public_key)
                    ),
                    secret_key=wallet.seed,
                    account_id=wallet.classic_address,
                )
            )
        return result
