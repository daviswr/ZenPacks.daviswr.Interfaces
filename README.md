# ZenPacks.daviswr.Interfaces

My own take on the ethernetCsmacd family of templates to include multicast rates, broadcast rates, drop rastes, queue length, and more thresholds.

## Important

This will *DOUBLE* the number of datapoints polled per interface which could have a sizeable effect on the performance of your Zenoss system if you monitor a non-trivial number of interface-dense devices, like switches.

Unicast packet rate graphs will be reset due to a typo in Zenoss' original template naming. On 4.2.5, a combination of `find` and `rename` could be used to rename all `ifInUcastPackets_ifInUcastPackets.rrd` files to `ifInUcastPkts_ifInUcastPkts.rrd` and `ifOutUcastPackets_ifOutUcastPackets.rrd` to `ifOutUcastPkts_ifOutUcastPkts.rrd`. I don't know how one would go about renaming datapoints on 5+.

## zProperties

Doesn't add anything new (yet), but sets the following if not already:

* /zInterfaceMapIgnoreNames
  * `(ch.|docker|Extension|Filter|ISATAP|Kernel Debug|mgi|Miniport|RAS Async|Scheduler|Software Loopback|veth|vlan)`
* /zInterfaceMapIgnoreTypes
  * `(100BaseVG|Encapsulation Interface|HIPPI|IEEE 802.3ad Link Aggregate|Layer 2 Virtual LAN using 802.1Q|modem|Other|ppp|propVirtual|softwareLoopback|Voice)`
* /Network/Firewall/ScreenOS/zInterfaceMapIgnoreTypes
  * `(Encapsulation Interface|modem|softwareLoopback)`

Really just my personal preference.

## Usage

Modeling is handled by `zenoss.snmp.InterfaceMap` already, this overrides the ethernetCsmacd template at:

* /
* /Network/Switch/Dell
* /Server/Windows

And ethernetCsmacd_64 at:

* /
* /Network

Existing templates defined at those classes will be renamed during the install process.

If there are transforms in place for the /Status/Perf and /Perf/Interface event classes, new ones in this ZenPack won't be installed. Clear them before installation or apply the code snippets in the `transforms` directory of this repository manually.
The revised /Status/Perf transform should help with spurious ifOperStatus ValueChangeThreshold events.
