import hassapi

class Room(hassapi.Hass):
    ONE_PRESS = 1002
    ONE_HOLD = 1001
    ONE_RELEASE = 1003
    ZERO_PRESS = 2002
    ZERO_HOLD = 2001
    ZERO_RELEASE = 2003

    def initialize(self):
        self.log('Initializing Room')
        self.current_scene = self.args['scenes']['off']

        self.listen_event(self.on_call_service, 'call_service')
        self.listen_event(self.on_state_changed, 'state_changed')
        self.listen_event(self.on_deconz_event, 'deconz_event')

    def on_call_service(self, event, data, kwargs):
        if data['domain'] != 'scene' or data['service'] != 'turn_on':
            return

        # Sometimes the entity_id is a string, sometimes an array of strings, depending
        # on how the scene was activated. Normalize it to an array.
        scenes = data['service_data']['entity_id']
        if isinstance(scenes, str):
            scenes = [scenes]

        for scene in scenes:
            if scene in self.args['scenes'].values():
                self.current_scene = scene
                self.log('New scene: ' + scene)

    def on_state_changed(self, event, data, kwargs):
        button = data['entity_id']

        if button.startswith('sensor.'):
            button = button[7:]

        if button.endswith('_action'):
            button = button[:-7]

        if button in self.args['buttons']:
            self.log('{}: {}'.format(button, data['new_state']['state']))

            if data['new_state']['state'] == 'on':
                if self.current_scene == self.args['scenes']['one']:
                    self.turn_on(self.args['scenes']['off'], transition = 0)
                else:
                    self.turn_on(self.args['scenes']['one'], transition = 0)

            if data['new_state']['state'] == 'off':
                if self.current_scene == self.args['scenes']['zero']:
                    self.turn_on(self.args['scenes']['off'], transition = 0)
                else:
                    self.turn_on(self.args['scenes']['zero'], transition = 0)

    def on_deconz_event(self, event, data, kwargs):
        button = data['id']

        if button in self.args['buttons']:
            self.log('{}: {}'.format(button, data['event']))

            if data['event'] == self.ONE_PRESS:
                if self.current_scene == self.args['scenes']['one']:
                    self.turn_on(self.args['scenes']['off'], transition = 0)
                else:
                    self.turn_on(self.args['scenes']['one'], transition = 0)

            if data['event'] == self.ZERO_PRESS:
                if self.current_scene == self.args['scenes']['zero']:
                    self.turn_on(self.args['scenes']['off'], transition = 0)
                else:
                    self.turn_on(self.args['scenes']['zero'], transition = 0)
