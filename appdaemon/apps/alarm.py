import datetime
import hassapi

class Alarm(hassapi.Hass):
    def initialize(self):
        self.next_alarms = {}
        self.waking = None
        self.last_color = None
        self.last_brightness = None
        self.log('Initializing Alarm')
        self.listen_event(self.on_state_changed, 'state_changed')

        for entity in self.args['alarms']:
            self.next_alarms[entity] = self.get_alarm(entity)

        self.log('Next alarms: {}'.format(self.next_alarms))
        self.run_every(self.alarm_check, self.datetime(), interval=60)
        self.alarm_check()

    def on_state_changed(self, event, data, kwargs):
        entity = data['entity_id']

        if entity not in self.args['alarms']:
            return
        
        date = self.convert_utc(data['new_state']['state'])
        self.next_alarms[entity] = date
        self.log('New alarm: {} on {}'.format(entity, date))

    def alarm_check(self, args = None):
        if self.waking is not None:
            self.light()
            return

        # Check that we're in a waking period
        if not self.now_is_between(self.args['time']['start'], self.args['time']['end']):
            return

        start = self.parse_datetime(self.args['time']['start'], aware = True)
        end = self.parse_datetime(self.args['time']['end'], aware = True)

        # Check all alarms
        start_waking = None

        for entity, alarm in self.next_alarms.items():
            if alarm is None:
                self.log('Alarm {} not set'.format(entity))
                return

            if alarm > end:
                self.log('Alarm {} at {} outside waking period'.format(entity, alarm))
                return

            alarm_offset = abs((alarm - datetime.timedelta(minutes = 10) - self.get_now()).total_seconds())
            
            if alarm_offset < 60:
                self.log('Alarm {} will go off soon'.format(entity))
                if not start_waking or alarm < start_waking:
                    start_waking = alarm

        if start_waking is not None:
            self.log('Start waking alarm: {}'.format(start_waking))
            self.waking = start_waking
            self.light()

    def light(self):
        if self.waking is None:
            return

        entity = self.args['light']
        start = self.waking - datetime.timedelta(minutes = 10)
        end = self.waking + datetime.timedelta(minutes = 10)

        if self.get_now() > end:
            self.turn_on(self.args['end_scene'], transition = 10)
            self.clear()
            return

        state = self.get_state(entity, 'all');
        current_brightness = state['attributes']['brightness'] or 0
        current_color = state['attributes']['color_temp_kelvin'] or 0
        self.log('Current color: {}, current brightness: {}'.format(current_color, current_brightness))

        # Stop ramping when we turn the lights on or off manually
        brightness_shift = 0 if self.last_brightness is None else abs(self.last_brightness - current_brightness)
        color_shift = 0 if self.last_color is None else abs(self.last_color - current_color)
        self.log('Color shift: {}, brightness shift: {}'.format(color_shift, brightness_shift))

        if color_shift > 2:
            self.log('Stop waking (color shift: {})'.format(color_shift))
            self.clear()
            return

        if brightness_shift > 0:
            self.log('Stop waking (brightness shift: {})'.format(brightness_shift))
            self.clear()
            return

        color = self.ease(start, end, 2000, 3000)
        brightness = self.ease(start, end, 1, 254)
        self.log('Turning on {} with color {} and brightness {}'.format(entity, color, brightness))
        self.turn_on(entity, color_temp_kelvin = color, brightness = brightness, transition = 10)
        self.last_color = color
        self.last_brightness = brightness

    def ease(self, start, end, min, max):
        stamp_start = start.timestamp()
        stamp_end = end.timestamp()
        stamp_now = self.get_now_ts()
        value = (stamp_now - stamp_start) / (stamp_end - stamp_start)

        # Cubic ease
        value = value * value * value;

        result = min + ((max - min) * value)
        
        if result > max:
            result = max

        return int(result)

    def get_alarm(self, entity):
        state = self.get_state(entity)
        if state == 'unavailable':
            return None
        return self.convert_utc(state)

    def clear(self):
        self.waking = None
        self.last_color = None
        self.last_brightness = None
