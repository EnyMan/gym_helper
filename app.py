import streamlit as st
from app_state import AppState, Workout
import numpy as np
from local_storage import StLocalStorage
import json

st_ls = StLocalStorage()


if "app_data" not in st.session_state:
    st.session_state["app_data"] = AppState()

if "recomended_weight_multiplier" not in st.session_state:
    st.session_state["recomended_weight_multiplier"] = 55


def save_data():
    st_ls.set(
        "app_data",
        {
            "recomended_weight_multiplier": st.session_state["recomended_weight_multiplier"],
            "data": st.session_state["app_data"].to_dict(),
        },
    )
    st.write(st_ls.get("app_data"))


def load_data():
    local_app_data = st_ls.get("app_data")
    if local_app_data is None:
        print("No data to load")
        return
    print("Loading data")
    st.write(local_app_data)
    st.session_state["recomended_weight_multiplier"] = local_app_data["recomended_weight_multiplier"]
    st.session_state["app_data"] = AppState.from_dict(local_app_data["data"])


def get_last_workout_metrics(workout: Workout):
    sets = len(workout.sets)
    if len(workout.sets) == 0:
        return 0, 0.0, 0.0
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
            bar_data.append(
                {
                    "weight": workout.to_pandas().weight.sum(),
                    "reps": workout.to_pandas().reps.sum(),
                }
            )
    return bar_data


st_ls.get("app_data")

st.write(st_ls.get("app_data"))

st.sidebar.title("Gym Helper")

st.sidebar.markdown("Some text to explain all the stuff")

st.sidebar.markdown("## Settings")

st.session_state["recomended_weight_multiplier"] = st.sidebar.slider(
    "1RM Percentage", 30, 85, st.session_state["recomended_weight_multiplier"], 1
)

st.sidebar.markdown("## Save/Load data")
sidebar_columns = st.sidebar.columns(2)
sidebar_columns[0].button("Save", use_container_width=True, on_click=save_data)
sidebar_columns[1].button("Load", use_container_width=True, on_click=load_data)

st.sidebar.download_button(
    "Download data",
    json.dumps(
        {
            "recomended_weight_multiplier": st.session_state["recomended_weight_multiplier"],
            "data": st.session_state["app_data"].to_dict(),
        }
    ),
    "gymerr.json",
)

st.title("Gym Helper")


tab1, tab2 = st.tabs(["🗃 Data", "📈 Chart"])


def _update_exercise(exercise_name, max_weight):
    st.session_state["app_data"].exercises[exercise_name].max_weight = max_weight


with tab1:
    st.header("Add new Exercise")

    with st.popover("Add/Update Exercise"):
        exercise = st.text_input("Name of the Exercise")
        max_weight = st.number_input(
            "Max Weight", value=0.0, min_value=0.0, max_value=200.0, step=0.5
        )
        if st.button("Submit", key="submit_exercise"):
            st.session_state["app_data"].add_exercises(exercise, max_weight)

    for exercise_name, exercise in st.session_state["app_data"].exercises.items():
        header_column1, header_column2 = st.columns(2, vertical_alignment="bottom")
        with header_column1:
            st.header(f"{exercise_name} - {len(exercise.workouts)} workouts")
            st.text(
                f"Recomended weight: {round(exercise.max_weight * st.session_state['recomended_weight_multiplier'] / 100)}"
            )
        with header_column2:
            with st.popover("Exercise Settings"):
                st.number_input(
                    "Max Weight",
                    value=exercise.max_weight,
                    min_value=0.0,
                    max_value=200.0,
                    step=0.5,
                    key=f"max_weight_{exercise_name}",
                    on_change=lambda: _update_exercise(exercise_name, st.session_state[f"max_weight_{exercise_name}"]),
                )
        if len(exercise.workouts) > 0:
            col1, col2, col3 = st.columns(3)
            last_sets, last_mean_weight, last_mean_reps = get_last_workout_metrics(
                exercise.workouts[-1]
            )
            previous_sets, previous_mean_weight, previous_mean_reps = (
                get_last_workout_metrics(exercise.workouts[-2])
                if len(exercise.workouts) > 1
                else (0, 0, 0)
            )
            col1.metric("Sets", last_sets, delta=last_sets - previous_sets)
            col2.metric(
                "Average Weight",
                last_mean_weight,
                delta=last_mean_weight - previous_mean_weight,
            )
            col3.metric(
                "Average Reps",
                last_mean_reps,
                delta=last_mean_reps - previous_mean_reps,
            )
        exercise_add_column, exercise_set_column, _ = st.columns([1, 1, 3])
        with exercise_add_column:
            if st.button("Add Workout", key=f"add_workout_{exercise_name}"):
                exercise.record_workout(Workout())
                st.rerun()
        with exercise_set_column:
            with st.popover("Record Set", disabled=len(exercise.workouts) == 0):
                weight = st.number_input(
                    "Weight",
                    value=float(
                        round(
                            exercise.max_weight
                            * st.session_state["recomended_weight_multiplier"]
                            / 100
                        )
                    ),
                    min_value=0.0,
                    max_value=200.0,
                    step=1.0,
                    key=f"weight_{exercise_name}",
                )
                reps = st.number_input(
                    "Reps",
                    value=0,
                    min_value=0,
                    max_value=100,
                    step=1,
                    key=f"reps_{exercise_name}",
                )
                if st.button("Submit", key=f"submit_workout_{exercise_name}"):
                    exercise.workouts[-1].add_set(weight, reps)
                    st.rerun()

with tab2:
    for exercise_name, exercise in st.session_state["app_data"].exercises.items():
        st.header(exercise_name)
        st.scatter_chart(
            prepare_scatter_data(exercise), x_label="Reps", y_label="Weight"
        )
        st.bar_chart(prepare_bar_data(exercise), x_label="Workout", y_label="Reps")
