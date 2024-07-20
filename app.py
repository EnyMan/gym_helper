import streamlit as st
from streamlit_local_storage import LocalStorage
from app_state import AppState, Workout
from streamlit_datalist import stDatalist
import matplotlib.pyplot as plt
import numpy as np

localS = LocalStorage()

if "app_data" not in st.session_state:
    st.session_state["app_data"] = AppState()


def save_data():
    localS.setItem("app_data", st.session_state["app_data"].to_dict())

def load_data():
    local_app_data = localS.getItem("app_data")
    st.session_state["app_data"] = AppState.from_dict(local_app_data)

@st.experimental_dialog("Add Exercise")
def add_exercise():
    # exercise = st.text_input("Exercise Name")
    exercise = stDatalist("This datalist is...", list(st.session_state["app_data"].exercises.keys()))
    max_weight = st.number_input("Max Weight", value=0.0, min_value=0.0, max_value=200.0, step=0.5)
    if st.button("Submit", key="submit_exercise"):
        st.session_state["app_data"].add_exercises(exercise, max_weight)
        st.rerun()

def get_last_workout_metrics(workout: Workout):
    sets = len(workout.sets)
    weight = np.mean([set_.weight for set_ in workout.sets])
    reps = np.mean([set_.reps for set_ in workout.sets])

    if np.isnan(weight):
        weight = 0.0
    if np.isnan(reps):
        reps = 0.0

    return sets, weight, reps

def prepare_scatter_data(exercise):
    scatter_data = []
    for workout in exercise.workouts:
        for set in workout.sets:
            scatter_data.append({"weight": set.weight, "reps": set.reps})
    return scatter_data

def prepare_bar_data(exercise):
    bar_data = []
    for workout in exercise.workouts:
        if len(workout.sets) > 0:
            bar_data.append({"weight": workout.to_pandas().weight.sum(), "reps": workout.to_pandas().reps.sum()})
    return bar_data

st.sidebar.title('Gym Helper')

sidebar_columns = st.sidebar.columns(2)
sidebar_columns[0].button('Save', use_container_width=True, on_click=save_data)
sidebar_columns[1].button('Load', use_container_width=True, on_click=load_data)

st.title('Gym Helper')

tab1, tab2 = st.tabs(["🗃 Data", "📈 Chart"])

# st.write(st.session_state["app_data"].to_dict())

with tab1:
    st.header("Add new Exercise")

    if st.button("Add/Update Exercise"):
        add_exercise()

    for exercise_name, exercise in st.session_state["app_data"].exercises.items():
        st.header(f"{exercise_name} - {len(exercise.workouts)} workouts")
        st.text(f"Recomended weight: {round(exercise.max_weight*0.55)}")
        if len(exercise.workouts) > 0:
            col1, col2, col3 = st.columns(3)
            last_sets, last_mean_weight, last_mean_reps = get_last_workout_metrics(exercise.workouts[-1])
            previous_sets, previous_mean_weight, previous_mean_reps = get_last_workout_metrics(exercise.workouts[-2]) if len(exercise.workouts) > 1 else (0, 0, 0)
            col1.metric("Sets", last_sets, delta=last_sets-previous_sets)
            col2.metric("Average Weight", last_mean_weight, delta=last_mean_weight-previous_mean_weight)
            col3.metric("Average Reps", last_mean_reps, delta=last_mean_reps-previous_mean_reps)
        # st.text(f"Current workout has: {len(exercise.workouts[-1].sets)} sets with {np.mean([set_.weight for set_ in exercise.workouts[-1].sets])} average weight and {np.mean([set_.reps for set_ in exercise.workouts[-1].sets])} average reps")
        exercise_add_column, exercise_set_column, _ = st.columns([1,1,3])
        with exercise_add_column:
            if st.button("Add Workout", key=f"add_workout_{exercise_name}"):
                exercise.record_workout(Workout())
        # if st.button("Record Workout", key=f"record_workout_{exercise_name}"):
            # record_workout(exercise)
        # st.write(f"Exercise: {exercise}, max weight: {exercise.max_weight}")
        with exercise_set_column:
            with st.popover("Record Set", disabled=len(exercise.workouts) == 0):
                weight = st.number_input("Weight", value=0.0, min_value=0.0, max_value=200.0, step=0.5, key=f"weight_{exercise_name}")
                reps = st.number_input("Reps", value=0, min_value=0, max_value=100, step=1, key=f"reps_{exercise_name}")
                if st.button("Submit", key=f"submit_workout_{exercise_name}"):
                    exercise.workouts[-1].add_set(weight, reps)

with tab2:
    for exercise_name, exercise in st.session_state["app_data"].exercises.items():
        st.header(exercise_name)
        st.scatter_chart(prepare_scatter_data(exercise), x_label="Reps", y_label="Weight")
        st.bar_chart(prepare_bar_data(exercise), x_label="Workout", y_label="Reps")
        # st.write(list(map(lambda x: x.to_pandas(), exercise.workouts)))
