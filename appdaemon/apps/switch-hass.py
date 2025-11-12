import hassapi

class SwitchHass(hassapi.Hass):
    def initialize(self):
        self.log('Initializing Switch Hass')
        self.listen_event(self.on_state_changed, 'state_changed')

    def on_state_changed(self, event, data, kwargs):
        button = data['entity_id']

        if button.startswith('sensor.'):
            button = button[7:]

        if button.endswith('_action'):
            button = button[:-7]

        if button in self.args['buttons']:
            self.log('{}: {}'.format(button, data['new_state']['state']))

            if data['new_state']['state'] == 'on':
                self.turn_on(self.args['target'])

            if data['new_state']['state'] == 'off':
                self.turn_off(self.args['target'])
