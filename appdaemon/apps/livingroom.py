import hassapi
import time

class LivingRoom(hassapi.Hass):
    tracked_scenes = [
        'scene.woonkamer_uit',
        'scene.woonkamer_fel',
        'scene.woonkamer_avond',
        'scene.woonkamer_nacht',
    ]

    scene_overrides = {
        'sensor.smart_button_eettafel_action': {False: 'scene.eettafel_avond', True: 'scene.eettafel_fel'},
        'sensor.smart_button_keuken_action': {False: 'scene.keuken_avond', True: 'scene.keuken_fel'},
    }

    def initialize(self):
        self.log('Initializing LivingRoom')
        self.current_scene = 'scene.woonkamer_uit'
        self.current_overrides = {}
        self.cycled = False

        for button in self.scene_overrides:
            self.current_overrides[button] = False

        self.listen_event(self.on_call_service, 'call_service')
        self.listen_event(self.on_state_changed, 'state_changed')

    def on_call_service(self, event, data, kwargs):
        if data['domain'] != 'scene' or data['service'] != 'turn_on':
            return

        # Sometimes the entity_id is a string, sometimes an array of strings, depending
        # on how the scene was activated. Normalize it to an array.
        scenes = data['service_data']['entity_id']
        if isinstance(scenes, str):
            scenes = [scenes]

        for scene in scenes:
            if scene in self.tracked_scenes:
                self.current_scene = scene
                self.log('New scene: ' + scene)

                # If the new scene is woonkame_avond, apply overrides
                if scene == 'scene.woonkamer_avond':
                    for button in self.current_overrides:
                        self.turn_on(self.scene_overrides[button][self.current_overrides[button]])
                else:
                    # Reset all overrides
                    for button in self.current_overrides:
                        self.current_overrides[button] = False

    def on_state_changed(self, event, data, kwargs):
        button = data['entity_id']

        # Handle zithoek button
        if button == 'sensor.smart_button_zithoek_action':
            self.log('{}: {}'.format(button, data['new_state']['state']))

            # Short click - toggle
            if data['new_state']['state'] == 'release':
                if self.cycled == False:
                    self.handle_toggle()
                else:
                    self.cycled = False
                return

            # Long click - cycle scenes
            if data['new_state']['state'] == 'hold' and self.cycled == False:
                self.handle_cycle()
                self.cycled = True
                return

        # Handle override buttons
        if button in self.scene_overrides and data['new_state']['state'] == 'release':
            self.log('{}: release'.format(button))
            self.handle_override(button)

    def handle_toggle(self):
        if self.current_scene == 'scene.woonkamer_uit':
            self.turn_on('scene.woonkamer_avond')
            self.log('Toggle on')
        else:
            self.turn_on('scene.woonkamer_uit')
            self.log('Toggle off')

    def handle_cycle(self):
        if self.current_scene == 'scene.woonkamer_uit':
            return

        # Skip first scene when cycling
        scenes = self.tracked_scenes[1:]
        index = scenes.index(self.current_scene)
        index = (index + 1) % len(scenes)

        self.turn_on(scenes[index])
        self.log('Cycle scene: ' + scenes[index])

    def handle_override(self, button):
        if self.current_overrides[button]:
            self.current_overrides[button] = False
            self.turn_on(self.current_scene)
            self.log('Disable override ' + button)
        else:
            self.current_overrides[button] = True
            self.turn_on(self.scene_overrides[button][True])
            self.log('Enable override ' + button)
