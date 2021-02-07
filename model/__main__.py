import simpy

from .mesh import Mesh
from .transmitter import Transitter, TxMode
from .receiver import Receiver

env  = simpy.Environment()
mesh = Mesh(env, 10, 10)
tx   = Transitter(env, mesh.ingress, max_send=10000, bursts=(8, 10), mode=TxMode.UNIQUE)
rx   = Receiver(env, mesh.egress)
env.run()

# Check all generated messages were captured
sent     = sorted(tx.sent,     key=lambda x: x.id)
received = sorted(rx.received, key=lambda x: x[1].id)

print("")
print("="*60)
print("")
print(f"Checking for consistency - #TX: {len(sent)}, #RX: {len(received)}")
assert len(sent) == len(received)
for tx_pkt, (rx_time, rx_pkt) in zip(sent, received):
    if tx_pkt != rx_pkt:
        print(
            f" - {tx_pkt.id:04d} - Mismatch on packet created at {tx_pkt.created},"
            f" received at {rx_time}"
        )
    assert tx_pkt == rx_pkt
print("")
print("="*60)
print("")
print(f"Mesh utilisation ({mesh.rows} x {mesh.columns}):")
print("")
for row in range(mesh.rows+1):
    # Print network statistics first
    print(f"Network  {row} - {mesh.networks[row].utilisation:>#5.2f} %")
    # Print element statistics
    if row >= mesh.rows: break
    el_str = [f"Elements {row} -"]
    for elem in mesh.elements[row]:
        el_str.append(f"{elem.utilisation:>#5.2f} %")
    print(" ".join(el_str))
print("")
print("="*60)
print("")
print(f"Simulation took {env.now} cycles - {len(rx.received)/env.now:4.2f} msg/cycle")
print("")
print("="*60)
print("")
