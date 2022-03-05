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
    UnixSocketAddress unixSocketAddress;
    UnixSocketChannel channel;

    @Override
    public void open(String address) throws IOException
    {
        System.out.printf("Opening unix domain socket for address %s%n", address);
        this.unixSocketAddress = new UnixSocketAddress(address);
        this.channel = UnixSocketChannel.open(this.unixSocketAddress);
    }

    @Override
    public void write(byte[] output) throws IOException
    {
        String writeContents = new String(output.clone());
        System.out.println("Writing content to unix domain socket:");
        System.out.println(writeContents);
        this.channel.write(ByteBuffer.wrap(output));
    }

    @Override
    public int read(byte[] inputBuffer) throws IOException
    {
        ByteBuffer inputByteBuffer = ByteBuffer.wrap(inputBuffer);
        int bytesRead = this.channel.read(inputByteBuffer);
        System.arraycopy(inputByteBuffer.array(), 0, inputBuffer, 0, inputByteBuffer.capacity());

        String readContents = new String(inputBuffer.clone());
        System.out.println("Read content from unix domain socket:");
        System.out.println(readContents);

        return bytesRead;
    }

    @Override
    public void close() throws IOException
    {
        System.out.println("Closing unix domain socket");
        this.channel.close();
    }
}
