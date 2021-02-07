import click
import simpy

from .base import Base, Verbosity
from .mesh import Mesh
from .transmitter import Transitter, TxMode
from .receiver import Receiver

@click.command()
# Mesh configuration
@click.option("-r", "--rows", type=int, default=2, help="How many rows in the mesh")
@click.option("-c", "--cols", type=int, default=2, help="How many columns in the mesh")
# Simulation setup
@click.option("-m", "--messages", type=int, default=100,                                   help="How many messages to send")
@click.option("-p", "--pattern",  type=click.Choice(["unique", "random"]), default="unique", help="Transmitter pattern")
# Verbosity controls
@click.option("--quiet", default=False, count=True, help="Only show warning & error messages")
@click.option("--debug", default=False, count=True, help="Enable debug messages")
def main(
    # Mesh configuration
    rows, cols,
    # Simulation setup
    messages, pattern,
    # Verbosity controls
    quiet, debug,
):
    # Setup verbosity
    if   quiet: Base.set_verbosity(Verbosity.WARN )
    elif debug: Base.set_verbosity(Verbosity.DEBUG)
    else      : Base.set_verbosity(Verbosity.INFO )

    env  = simpy.Environment()
    mesh = Mesh(env, rows, cols)
    rx   = Receiver(env, mesh.egress)
    tx   = Transitter(
        env,
        mesh.ingress,
        max_send=messages,
        bursts  =(8, 10),
        mode    =TxMode[pattern.upper()]
    )
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

if __name__ == "__main__":
    main()
