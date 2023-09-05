#!/usr/bin/env python
import asyncio
import logging
import socket

from handlers.action_registry import ActionRegistry

from opensearch_sdk_py.transport.outbound_message_request import OutboundMessageRequest
from opensearch_sdk_py.transport.outbound_message_response import (
    OutboundMessageResponse,
)
from opensearch_sdk_py.transport.stream_input import StreamInput
from opensearch_sdk_py.transport.tcp_header import TcpHeader


async def handle_connection(conn, loop):
    try:
        conn.setblocking(False)

        while raw := await loop.sock_recv(conn, 1024 * 10):
            input = StreamInput(raw)
            print(f"\nreceived {input}, {len(raw)} byte(s)\n\t#{str(raw)}")

            header = TcpHeader().read_from(input)
            print(f"\t{header}")

            if header.is_request():
                request = OutboundMessageRequest().read_from(input, header)
                if request.thread_context_struct and request.thread_context_struct.request_headers:
                    print(f"\t{request.thread_context_struct}")
                if request.features:
                    print(f"\tfeatures: {request.features}")
                if request.action:
                    print(f"\taction: {request.action}")

                output = ActionRegistry.handle_request(request, input)
                if output is None:
                    print(
                        f"\tparsed action {header}, haven't yet written what to do with it"
                    )
            else:
                response = OutboundMessageResponse().read_from(input, header)
                # TODO: Error handling
                if response.is_error():
                    output = None
                    print(
                        f"\tparsed {header}, this is an ERROR response"
                    )
                else:
                    output = ActionRegistry.handle_response(response, input)
                    if output is None:
                        print(
                            f"\tparsed {header}, this is a response to something I haven't sent"
                        )
            if output:
                await loop.sock_sendall(conn, output.getvalue())

    except Exception as ex:
        logging.exception(ex)
    finally:
        conn.close()


async def run_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("localhost", 1234))
    server.setblocking(False)
    server.listen()

    loop = asyncio.get_event_loop()

    print(f"listening, {server}")
    while True:
        conn, _ = await loop.sock_accept(server)
        print(f"got a connection, {conn}")
        loop.create_task(handle_connection(conn, loop))


asyncio.run(run_server())
