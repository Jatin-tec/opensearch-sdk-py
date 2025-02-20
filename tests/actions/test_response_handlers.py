#
# Copyright OpenSearch Contributors
# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.
#

import unittest
from typing import Optional

from opensearch_sdk_py.actions.internal.register_rest_actions_response_handler import RegisterRestActionsResponseHandler
from opensearch_sdk_py.actions.request_handler import RequestHandler
from opensearch_sdk_py.actions.response_handlers import ResponseHandlers
from opensearch_sdk_py.extension import Extension
from opensearch_sdk_py.transport.acknowledged_response import AcknowledgedResponse
from opensearch_sdk_py.transport.outbound_message_request import OutboundMessageRequest
from opensearch_sdk_py.transport.outbound_message_response import OutboundMessageResponse
from opensearch_sdk_py.transport.stream_input import StreamInput
from opensearch_sdk_py.transport.stream_output import StreamOutput


class TestResponseHandlers(unittest.TestCase):
    class MyExtension(Extension):
        def __init__(self) -> None:
            super().__init__("test-extension")
            self.test = ""

    def setUp(self) -> None:
        self.extension = TestResponseHandlers.MyExtension()
        self.response_handlers = ResponseHandlers(self.extension)
        next_handler = FakeRequestHandler(self.extension)
        self.response_handlers.register(123, RegisterRestActionsResponseHandler(next_handler))

    def test_register_handlers(self) -> None:
        self.assertEqual(len(self.response_handlers), 1)
        self.assertIsInstance(self.response_handlers[123], RegisterRestActionsResponseHandler)

    def test_handle(self) -> None:
        response = OutboundMessageResponse(request_id=123)
        input = StreamInput(bytes(AcknowledgedResponse(status=True)))
        output = self.response_handlers.handle(response, input)
        self.assertEqual(len(self.response_handlers), 0)
        self.assertEqual(output, None)
        self.assertEqual(self.extension.test, "modified")


class FakeRequestHandler(RequestHandler):
    def __init__(self, extension: Extension) -> None:
        super().__init__("test-extension", extension)

    def handle(self, request: OutboundMessageRequest, input: StreamInput = None) -> Optional[bytes]:
        return None

    def send(self) -> StreamOutput:
        self.extension.test = "modified"
        return None
