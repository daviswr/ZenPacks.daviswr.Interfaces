# SET OPERSTATUS ON IPINTERFACE COMPONENT
if evt.eventKey == 'ifOperStatus_ifOperStatus|ifOperStatusChange':
    evt._action = 'drop'
    operStatus = int(float(getattr(evt, 'current', '0')))
    if component is not None:
        if component.operStatus != operStatus:
            @transact
            def updateDb():
                component.operStatus = operStatus
            updateDb()
