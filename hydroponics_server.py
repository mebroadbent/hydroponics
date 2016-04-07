#!/usr/bin/python

""" Hydroponics controller that runs a RPyC server and can thus be controlled
by another process, such as the web application.

You should start the server (by running this script) before starting the
web application.

The web application does not control the hardware directly because we want
only one instance of the HydroponicsController running at the same time,
but the web server creates a new thread for every connection.

"""

import datetime

import rpyc
from apscheduler.schedulers.background import BackgroundScheduler

from hydroponics import HydroponicsController, MockHydroponicsController
from config import (PUMP_PIN, LIGHTS_PIN, PUMP_DEFAULT_ON, LIGHTS_DEFAULT_ON,
                    PUMP_TIME, LIGHTS_TIME_ON, LIGHTS_TIME_OFF, PORT)


class CustomizedHydroponicsService(hydroponics_controller, scheduler):
    class HydroponicsService(rpyc.Service):
        self.paused = False
        self.resume_time = None

        def exposed_is_paused(self):
            return self.paused

        def exposed_get_resumption_time(self):
            return self.resume_time

        def exposed_resume(self):
            """Resume regular operation of the hydroponics system."""

            self.paused = False
            try:
                scheduler.remove_job("resume")
            except JobLookupError:
                pass

            for job in ["pump", "lights on", "lights off"]:
                scheduler.resume_job(job)

            current_hour = datetime.datetime.now().time()
            time_on = datetime.time(LIGHTS_TIME_ON,0)
            time_off = datetime.time(LIGHTS_TIME_OFF,0)
            if current_hour > time_on and current_hour < time_off:
                h.lights_on()

        def exposed_pause(self, duration):
            """Pause the hydroponics system for duration."""

            self.paused = True
            self.resume_time = self.get_resumption_time(duration)
            h.lights_off()
            h.pump_off()

            for job in ["pump", "lights on", "lights off"]:
                scheduler.pause_job(job)

            scheduler.add_job(self.exposed_resume, 'date',
                              run_date=self.resume_time, id="resume")

        def get_resumption_time(self, pause_duration):
            # TO DO: Perform some type of validation of pause_duration?
            pause_datetime = datetime.timedelta(minutes=int(pause_duration))
            return datetime.datetime.now() + pause_datetime
    
    return HydroponicsService

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    kwargs = {"pump_pin": PUMP_PIN,
              "lights_pin": LIGHTS_PIN,
              "pump_default_on": PUMP_DEFAULT_ON,
              "lights_default_on": LIGHTS_DEFAULT_ON}
    
    with MockHydroponicsController(**kwargs) as h:
        # TODO: I should name jobid's here, so that I can pause and resume
        # them later as needed.
        scheduler.add_job(h.run_pump, 'interval', hours=1, args=(PUMP_TIME,),
                          id="pump")
        scheduler.add_job(h.lights_on,  'cron', hour=LIGHTS_TIME_ON,
                          id="lights on")
        scheduler.add_job(h.lights_off, 'cron', hour=LIGHTS_TIME_OFF,
                          id="lights off")
        scheduler.start()

        cs = CustomizedHydroponicsService(h, scheduler)
        t = rpyc.ThreadedServer(cs, port=PORT)

        try:
            t.start()
        finally:
            scheduler.shutdown()