"""Pure work screen calculations."""


class WorkService:
    def should_show_sync_button(
        self,
        has_variants: bool,
        has_analog_groups: bool,
    ) -> bool:
        return has_variants and not has_analog_groups
