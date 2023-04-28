import logging
from typing import Union, Optional, Any
from web3 import HTTPProvider
from web3_proxy_providers import HttpWithProxyProvider
from eth_typing import URI
from web3.types import RPCEndpoint, RPCResponse


class ZkSyncProvider(HTTPProvider):
    logger = logging.getLogger("ZkSyncProvider")

    def __init__(self, url: Optional[Union[URI, str]], proxy_url: Optional[str]):
        # request_kwargs param proxies: (optional) Dictionary mapping protocol to the URL of the proxy.
        super(ZkSyncProvider, self).__init__(endpoint_uri=url, request_kwargs={'timeout': 1000, 'proxies': {'http': proxy_url, 'https': proxy_url}})

    def make_request(self, method: RPCEndpoint, params: Any) -> RPCResponse:
        self.logger.debug(f"make_request: {method}, params : {params}")
        response = HTTPProvider.make_request(self, method, params)
        return response
