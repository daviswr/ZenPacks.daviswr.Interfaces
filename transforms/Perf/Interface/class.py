import re

DUPLEX_UNKNOWN = 1
DUPLEX_HALF = 2
DUPLEX_FULL = 3

current = float(getattr(evt, 'current', '0.0'))

# Determine direction
if evt.eventKey.startswith('ifHCOut') or evt.eventKey.startswith('ifOut'):
    direction = 'output'
elif evt.eventKey.startswith('ifHCIn') or evt.eventKey.startswith('ifIn'):
    direction = 'input'

# Zenoss 4.2 replaces / in evt.component with _
# even though it displays / in the event
match = re.search(r'^(\D{2})\D+(\d*_?\d*_?\d*)$', evt.component)
if match:
    evt.component = re.sub('_', '/', evt.component)
if_name = evt.component

# Find short name of interface, if possible
match = re.search(r'^(\D{2})\D+(\d*/?\d*/?\d*)$', if_name)
if match and 'Server' not in device.getDeviceClassPath():
    if_name_short = match.groups()[0] + match.groups()[1]
else:
    if_name_short = if_name

# Find interface's bandwidth to get utilization as percentage
# Also interface description and duplex
duplex = DUPLEX_UNKNOWN
speed = 0
descr = ''
for iface in device.os.interfaces():
    if iface.name() == if_name:
        duplex = iface.duplex
        speed = iface.speed
        if len(iface.description) > 0:
            descr = '(%s)' % (iface.description)
        break

# Throughput threshold
if (evt.eventKey == 'ifHCInOctets_ifHCInOctets|Throughput'
        or evt.eventKey == 'ifHCOutOctets_ifHCOutOctets|Throughput'
        or evt.eventKey == 'ifInOctets_ifInOctets|Throughput'
        or evt.eventKey == 'ifOutOctets_ifOutOctets|Throughput'):
    # Current value in bits
    current = current * 8
    if current > 1000000000:
        usage = '%3.1f Gbps' % (current / 1000000000)
    elif current > 1000000:
        usage = '%3.1f Mbps' % (current / 1000000)
    elif current > 1000:
        usage = '%3.1f Kbps' % (current / 1000)
    else:
        usage = '%3.1f bps' % (current)

    # Drop if interface speed unknown
    if 0 == speed:
        evt._action = 'drop'
    # Drop if gig+ interface linked at a lower speed
    # Will only work with some vendors
    elif ((evt.component.lower().startswith('g')
            or evt.component.lower().startswith('te')
            or evt.component.lower().startswith('x'))
            and current <= 100000000):
        evt._action = 'drop'
    # Drop if span port
    elif ' span' in descr.lower():
        evt._action = 'drop'
    else:
        util = (current / speed) * 100
        # If it thinks more than 100% of the link is in use,
        # it's not modeled correctly
        if util > 100:
            log.info(
                '%s %s speed modeled incorrectly',
                device.name(),
                if_name_short
                )
            # Model in background so transform isn't delayed
            #device.collectDevice(background=True)
            evt._action = 'drop'
        else:
            evt.summary = '%s %s %s utilization at %3.1f%% (%s)' % (
                if_name_short,
                descr,
                direction,
                util,
                usage
                )

# Broadcast/Multicast threshold
elif (evt.eventKey == 'ifHCInMulticastPkts_ifHCInMulticastPkts|Multicast'
      or evt.eventKey == 'ifHCInBroadcastPkts_ifHCInBroadcastPkts|Broadcast'
      or evt.eventKey == 'ifInMulticastPkts_ifInMulticastPkts|Multicast'
      or evt.eventKey == 'ifInBroadcastPkts_ifInBroadcastPkts|Broadcast'
      or evt.eventKey == 'ifInNUcastPkts_ifInNUcastPkts|Multicast'):
    traffic = evt.eventKey.split('|')[1].lower()
    evt.summary = '%s %s %s %s rate at %3.0f packets per second' % (
        if_name_short,
        descr,
        direction,
        traffic,
        current
        )
    # Drop if Port Channel interface
    if evt.component.startswith('Port-channel'):
        evt._action = 'drop'
    else:
        # Drop if port goes to another switch
        # Requires custom CDP/LLDP neighbor modeler
        for neighbor in device.neighbor_switches():
            if neighbor.location == evt.component:
                evt._action = 'drop'
                break

# Error threshold
elif (evt.eventKey == 'ifInErrors_ifInErrors|Errors'
      or evt.eventKey == 'ifOutErrors_ifOutErrors|Errors'):

    # Nothing we can do about errors on a half-duplex port
    if duplex == DUPLEX_HALF:
        evt._action = 'drop'
    # Hairpinned traffic on an F5 BIG-IP LTM causes input errors
    # Nothing to do about it
    elif device and 'F5' in device.getDeviceClassPath():
        evt._action = 'drop'
    else:
        if current < 1:
            current = current * 60
            time = 'minute'
        else:
            time = 'second'
        evt.summary = '%s %s experiencing %3.0f %s errors per %s' % (
            if_name_short,
            descr,
            current,
            direction,
            time
            )

# Discard threshold
elif (evt.eventKey == 'ifInDiscards_ifInDiscards|Drops'
      or evt.eventKey == 'ifOutDiscards_ifOutDiscards|Drops'):
    if current < 1:
        current = current * 60
        time = 'minute'
    else:
        time = 'second'
    evt.summary = '%s %s dropping %3.0f %s packets per %s' % (
        if_name_short,
        descr,
        current,
        direction,
        time
        )
