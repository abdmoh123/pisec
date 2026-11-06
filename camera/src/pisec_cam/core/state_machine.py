"""State machine implementation. Based off ArjanCode's implementation."""

from abc import ABC
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from enum import Enum, StrEnum

from pisec_cam.core.exceptions.state_machine import TransitionError

type _Transition[S, C] = tuple[S, Action[C], Guard[C] | None]

type Action[C] = Callable[[C], None]
type Guard[C] = Callable[[C], bool]


@dataclass(kw_only=True)
class SMContext(ABC):
    """Context for the state machine."""

    error: Exception | None = None


@dataclass
class StateMachine[S: Enum, E: Enum, C: SMContext]:
    """State machine implementation.

    Attributes:
        error_event: The event to trigger when an error occurs.
        transitions: The transitions between states.
    """

    error_event: E
    transitions: dict[tuple[S, E], list[_Transition[S, C]]] = field(
        default_factory=dict
    )

    def add_transition(
        self,
        from_state: S | Iterable[S],
        to_state: S,
        event: E,
        action: Action[C],
        guard: Guard[C] | None = None,
    ) -> None:
        """Adds a state-event pair (transition) to the state machine.

        Guards are used to allow conditional transitions for a given state.
        As good practice, one should have a fallback transition without a guard
        in case all other guards fail.

        Args:
            from_state: The state or list of states to transition from.
            to_state: The state to transition to.
            event: The event to trigger the transition.
            action: The action to perform when the transition is triggered.
            guard: A function to determine which state to transition to.
                Defaults to None as it's optional (unless you have more than one
                to_state transition registered).
        """
        if isinstance(from_state, StrEnum) or not isinstance(
            from_state, Iterable
        ):
            from_state = (from_state,)

        for state in from_state:
            key = (state, event)
            _ = self.transitions.setdefault(key, [])
            entry = (to_state, action, guard)
            # Ensure guarded transitions are run before unguarded
            if guard is None:
                self.transitions[key].append(entry)
            else:
                self.transitions[key].insert(0, entry)

    def handle_event(self, state: S, event: E, context: C) -> S:
        """Handles an event and returns the new state.

        Args:
            state: The current state.
            event: The event to handle.
            context: The context to pass to the action.

        Returns:
            The new state after running the relevant action.

        Raises:
            TransitionError: If the state-event pair wasn't registered.
        """
        if (state, event) not in self.transitions:
            raise TransitionError(
                f"No event {event.name} for state {state.name}"
            )

        for next_state, action, guard in self.transitions[(state, event)]:
            # Guarded transitions are always run before unguarded
            # see add_transition
            if guard is None or guard(context):
                try:
                    action(context)
                    return next_state
                except Exception as e:  # noqa: BLE001
                    # Handle any error that occurs
                    context.error = e
                    return self.handle_event(state, self.error_event, context)

        raise TransitionError(
            f"All guards failed for {event.name} in state {state.name}."
            + " Perhaps add a fallback without a guard next time."
        )

    def transition(
        self,
        from_state: S | Iterable[S],
        to_state: S,
        event: E,
        guard: Guard[C] | None = None,
    ) -> Callable[[Action[C]], Action[C]]:
        """Decorator for adding a function as a transition.

        Args:
            from_state: The state or list of states to transition from.
            to_state: The state to transition to.
            event: The event to trigger the transition.
            guard: A function to determine which state to transition to.

        Returns:
            The decorated function.
        """

        def wrapper(action: Action[C]) -> Action[C]:
            self.add_transition(from_state, to_state, event, action, guard)
            return action

        return wrapper
