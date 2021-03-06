"""
The purpose of the Scenario module is to provide the scenario class.
The scenario class should give a libraryuser the ability to simply
create new scenarios and implementing needed functions.
"""
import logging
import os

from abc import ABCMeta, abstractmethod
from threading import Thread, Timer
from time import sleep
from lid_ds.helpers import scenario_name
from .pout import add_run
from .container_run import container_run
from .recorder_run import record_container

logger = logging.getLogger(__name__)

class Scenario(metaclass=ABCMeta):
    @abstractmethod
    def exploit(self, *args, **kwargs):
        """
        Implement the exploit method in the derived class
        to add a hook that gets called when the exploit shall
        be executed.
        """
    @abstractmethod
    def wait_for_availability(self, container):
        """
        Implement a hook that returns once the container is ready
        """

    """
    The scenario class provides a baseclass to derive from
    in order to implement a custom security scenario
    """
    def __init__(
            self,
            image_name,
            port_mapping={},
            warmup_time=60,
            recording_time=300,
            behaviours=[],
            **kwargs
    ):
        """
        initialize all time sequences needed for the recording process
        as well es for statistically relevant execution
        """
        self.image_name = image_name
        self.port_mapping = port_mapping
        self.warmup_time = warmup_time
        self.behaviours = behaviours
        self.recording_time = recording_time
        self.execute_exploit = 'exploit_start_time' in kwargs
        print("Simulating with exploit " + str(self.execute_exploit))
        if not isinstance(self.warmup_time, (int, float)):
            raise TypeError("Warmup time needs to be an integer or float")
        if not isinstance(self.recording_time, (int, float)):
            raise TypeError("Recording time needs to be an integer or float")
        if self.execute_exploit:
            self.exploit_start_time = kwargs.get('exploit_start_time')
            if not isinstance(self.exploit_start_time, (int, float)):
                raise TypeError("Exploit start time needs to be an integer or float")

            if self.exploit_start_time > recording_time:
                raise ValueError(
                    "The start time of the exploit must be before the end of the recording!"
                    )
        self.current_threads = []

        self.name = scenario_name(self)
        add_run(self)
        """
        file = open("/data/runs.csv", "a+")
        if self.execute_exploit:
            file.write("{}, {}, {}, {}, {}, {}\n".format(self.image_name, self.name, str(self.execute_exploit), str(self.warmup_time), str(self.recording_time), str(self.exploit_start_time)))
        else:
            file.write("{}, {}, {}, {}, {}, {}\n".format(self.image_name, self.name, str(self.execute_exploit), str(self.warmup_time), str(self.recording_time), "none"))
        file.close()
        """

    def __call__(self, with_exploit=False):
        print('Simulating Scenario: {}'.format(self))
        with container_run({
            'image_name': self.image_name,
            'port_mapping': self.port_mapping
        }, self.wait_for_availability) as container:
            print('Start Normal Behaviours for Scenario: {}'.format(self.name))
            for behaviour in self.behaviours:
                thread_behaviour = Thread(target=behaviour, args=())
                thread_behaviour.start()
                self.current_threads.append(thread_behaviour)
            print('Warming up Scenario: {}'.format(self.name))
            sleep(self.warmup_time)
            print('Start Recording Scenario: {}'.format(self.name))
            with record_container(container, self.name) as recorder:
                # Do normal behaviour
                if self.execute_exploit:
                    print('Start Exploiting Scenario: {}'.format(self.name))
                    texploit = Timer(self.exploit_start_time, self.exploit, [container])
                    tannounce = Timer(self.exploit_start_time, print, ("Exploiting now"))
                    texploit.start()
                    tannounce.start()
                sleep(self.recording_time)

    def __repr__(self):
        if self.execute_exploit:
            return '<{} {} recording_time={} warmup_time={} exploit_start_time={}>'.format(
                self.__class__.__name__,
                self.name,
                self.recording_time,
                self.warmup_time,
                self.exploit_start_time
                )
        return '<{} {} recording_time={} warmup_time={}>'.format(
            self.__class__.__name__,
            self.name,
            self.recording_time,
            self.warmup_time,
            )

