from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
import pandas as pd

@dataclass_json
@dataclass
class Set:
    weight: float
    reps: int

@dataclass_json    
@dataclass
class Workout:
    sets: list[Set] = field(default_factory=list)

    def add_set(self, weight: float, reps: int) -> 'Workout':
        self.sets.append(Set(weight, reps))
        return self
    
    def to_pandas(self):
        # return [x.to_dict() for x in self.sets]
        return pd.DataFrame.from_records(map(lambda x: x.to_dict(), self.sets))

@dataclass_json
@dataclass
class Exercise:
    name: str
    max_weight: float
    workouts: list[Workout] = field(default_factory=list)	

    def record_workout(self, workout: Workout) -> 'Exercise':
        self.workouts.append(workout)
        return self

    def to_pandas(self):
        return [x.to_pandas() for x in self.workouts]

@dataclass_json
@dataclass
class AppState(object):
    exercises: dict[str, Exercise] = field(default_factory=dict)
    
    def add_exercises(self, exercise, max_weight) -> 'AppState':
        self.exercises[exercise] = Exercise(exercise, max_weight, [])
        return self