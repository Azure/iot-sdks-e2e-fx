// DIAGNOSTIC ONLY.  Opens a TLS connection to an MQTT endpoint, writes a
// syntactically valid MQTT 3.1.1 CONNECT, and reports whether the server
// answers.  The credentials are deliberately bogus: a CONNACK with a failure
// code still proves the server parsed the packet, which is the thing being
// measured.  delayMs controls whether CONNECT is written in the same tick the
// handshake completes (0) or in a later one.
const tls = require("tls");

const [host, servername, delayMsArg, maxVer] = process.argv.slice(2);
const delayMs = parseInt(delayMsArg || "0", 10);
const PORT = 8883;
const WAIT_MS = 20000;

function connectPacket(clientId) {
  const proto = Buffer.from("MQTT", "utf8");
  const parts = [];
  const str = (s) => {
    const b = Buffer.from(s, "utf8");
    const len = Buffer.alloc(2);
    len.writeUInt16BE(b.length, 0);
    return Buffer.concat([len, b]);
  };
  parts.push(str("MQTT"));
  parts.push(Buffer.from([0x04])); // protocol level 3.1.1
  parts.push(Buffer.from([0xc2])); // username + password + clean session
  const ka = Buffer.alloc(2);
  ka.writeUInt16BE(60, 0);
  parts.push(ka);
  parts.push(str(clientId));
  parts.push(str("diagUser"));
  parts.push(str("diagPass"));
  const body = Buffer.concat(parts);

  const lenBytes = [];
  let rem = body.length;
  do {
    let b = rem % 128;
    rem = Math.floor(rem / 128);
    if (rem > 0) b = b | 0x80;
    lenBytes.push(b);
  } while (rem > 0);

  return Buffer.concat([
    Buffer.from([0x10]),
    Buffer.from(lenBytes),
    body,
  ]);
  void proto;
}

const t0 = Date.now();
const el = () => Date.now() - t0;
let done = false;
const finish = (msg) => {
  if (done) return;
  done = true;
  console.log(`RESULT host=${host} max=${maxVer||"TLSv1.3"} delay=${delayMs}ms ${msg}`);
  try {
    sock.destroy();
  } catch (e) {
    /* ignore */
  }
  process.exit(0);
};

const sock = tls.connect(
  { host, port: PORT, servername, rejectUnauthorized: false, minVersion: "TLSv1.2", maxVersion: maxVer || "TLSv1.3" },
  () => {
    console.log(`  handshake ok proto=${sock.getProtocol()} at ${el()}ms`);
    const pkt = connectPacket("diagProbe" + process.pid);
    if (delayMs === 0) {
      sock.write(pkt);
      console.log(`  CONNECT written immediately at ${el()}ms`);
    } else {
      setTimeout(() => {
        sock.write(pkt);
        console.log(`  CONNECT written after delay at ${el()}ms`);
      }, delayMs);
    }
  }
);

sock.on("data", (d) => {
  finish(`SERVER ANSWERED ${d.length} bytes [${d.toString("hex")}] at ${el()}ms`);
});
sock.on("error", (e) => finish(`ERROR ${e.message} at ${el()}ms`));
sock.on("close", () => finish(`CLOSED WITH NO ANSWER at ${el()}ms`));
setTimeout(() => finish(`NO ANSWER within ${WAIT_MS}ms`), WAIT_MS);
