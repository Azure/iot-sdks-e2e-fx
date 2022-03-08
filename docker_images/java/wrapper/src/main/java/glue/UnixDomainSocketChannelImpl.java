// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

package glue;

import com.microsoft.azure.sdk.iot.device.hsm.UnixDomainSocketChannel;
import jnr.unixsocket.UnixSocketAddress;
import jnr.unixsocket.UnixSocketChannel;

import java.io.IOException;
import java.nio.ByteBuffer;

public class UnixDomainSocketChannelImpl implements UnixDomainSocketChannel
{
    private UnixSocketChannel channel;

    @Override
    public void open(String address) throws IOException
    {
        this.channel = UnixSocketChannel.open(new UnixSocketAddress(address));
    }

    @Override
    public void write(byte[] output) throws IOException
    {
        this.channel.write(ByteBuffer.wrap(output));
    }

    @Override
    public int read(byte[] inputBuffer) throws IOException
    {
        ByteBuffer inputByteBuffer = ByteBuffer.wrap(inputBuffer);
        int bytesRead = this.channel.read(inputByteBuffer);
        System.arraycopy(inputByteBuffer.array(), 0, inputBuffer, 0, inputByteBuffer.capacity());
        return bytesRead;
    }

    @Override
    public void close() throws IOException
    {
        this.channel.close();
    }
}
