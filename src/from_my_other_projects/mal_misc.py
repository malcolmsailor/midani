# def go_deep(func):
#     """Return function that runs on arbitarily deep lists/tuples/np arrays.
#
#     (To be exact, it runs on sequences [that match abc.Sequence] and np arrays.
#
#     Meant to be used as a decorator.
#
#     The decorated function should have just one argument and shouldn't return
#     anything (i.e., it should alter the items of the list in place).
#     """
#
#     def _sub(arg):
#         if isinstance(arg, (abc.Sequence, np.ndarray)):
#             for sub in arg:
#                 func(sub)
#         else:
#             func(arg)
#
#     return _sub
#
#
# def array_to_int_levels(array):
#     """Converts a 1-d np array to integer levels.
#
#     There has got to be a better (more efficient, more versatile) way
#     of doing this using np itself.
#     """
#     levels = list(np.unique(array))
#     levels = {level: levels.index(level) for level in levels}
#     return np.array([levels[val] for val in array])
#
#
# def dict_to_attributes(dict_, instance, exclude=(), process_kwargs=True):
#     for key, value in dict_.items():
#         if "kwargs" in key and value is None:
#             value = {}
#         if key in exclude:
#             continue
#         vars(instance)[key] = value
#
#
# def locals_to_attributes(local_dict, instance):
#     """Converts result of locals() call to attributes.
#
#     Should probably only be called at the outset of initializing the instance.
#     Excludes "self" and "__return__"; as far as I can tell nothing else
#     needs to be excluded.
#
#     Python 3.7 provides DataClass as an alternative to this approach.
#     """
#     dict_to_attributes(local_dict, instance, exclude=("self", "__return__"))
#
#
# def mod_index(iterable, i):
#     return iterable[i % len(iterable)]


def binary_search(num_list, num, not_found="none"):
    """Performs a binary search on a sorted list of numbers, returns index.

    Only works properly if the list is sorted, but does not check whether it is
    or not, this is up to the caller.

    Arguments:
        num_list: a sorted list of numbers.
        num: a number to search for.
        not_found: string. Controls what happens if the number is not in the
            list.
            - "none": None is returned.
            - "upper", "force_upper": upper index is returned
            - "lower", "force_lower": lower index is returned
            - "nearest": index to nearest item is returned
            If num is larger than all numbers in num_list,
                if "upper", "lower", "force_lower", or "nearest":
                    index to the last item of the list is returned.
                if "force_upper":
                    index to the next item past the end of the list is returned.
            If num is smaller than all numbers in num_list,
                if "upper", "force_upper", "lower", or "nearest":
                    0 is returned.
                if "force_lower":
                    -1 is returned.
            Default: None.

    returns:
        None if len(num_list) is 0
        None if num is not in num_list and not_found is "none"
        Integer index to item, or perhaps nearest item (depending on
            "not_found" keyword argument).
    """
    if not_found not in (
        "none",
        "upper",
        "force_upper",
        "lower",
        "force_lower",
        "nearest",
    ):
        raise ValueError(
            f"{not_found} is not a recognized value for argument " "'not_found'"
        )
    lower_i, upper_i = 0, len(num_list)
    if upper_i == 0:
        return None
    if num < num_list[0]:
        if not_found == "none":
            return None
        if not_found == "force_lower":
            return -1
        return 0
    if num > num_list[upper_i - 1]:
        if not_found == "none":
            return None
        if not_found == "force_upper":
            return upper_i
        return upper_i - 1

    while True:
        mid_i = (lower_i + upper_i) // 2
        n = num_list[mid_i]
        if n == num:
            return mid_i
        if mid_i == lower_i:
            if not_found == "none":
                return None
            if not_found in ("upper", "force_upper"):
                return upper_i
            if not_found in ("lower", "force_lower"):
                return lower_i
            return lower_i + (num_list[upper_i] - num < num - n)

        if n > num:
            upper_i = mid_i
        else:
            lower_i = mid_i


# def get_sorted_i(num_list, num, duplicates="first"):
#     """Returns the index at which a number should be inserted into a sorted
#     list to maintain sorting.
#
#     Only works properly if the list is sorted, but does not check whether it is
#     or not, this is up to the caller.
#
#     Args:
#         num_list: a sorted list of numbers.
#         num: a number to search for.
#
#     Keyword args:
#         duplicates: string. Controls behavior if `num` is already in `num_list`.
#             Possible values:
#                 - "first": returns index that will place the new item first.
#                 - "last": returns index that will place the new item last.
#                 - "none": returns None
#
#     Returns:
#         None if `num` is already in `num_list` and `duplicates` is "none"
#         integer otherwise.
#
#     Raises:
#         ValueError if duplicates not in ("first", "last", "none")
#     """
#
#     if len(num_list) == 0 or num < num_list[0]:
#         return 0
#     if num > num_list[-1]:
#         return len(num_list)
#
#     i = binary_search(num_list, num, not_found="upper")
#
#     if duplicates == "first" or num_list[i] != num:
#         return i
#     if duplicates == "none":
#         return None
#     if duplicates == "last":
#         try:
#             while num_list[i] == num:
#                 i += 1
#         except IndexError:
#             pass
#         return i
#     duplicate_vals = ("first", "last", "none")
#     raise ValueError(f"duplicates must be in {duplicate_vals}")
#
#
# def light_sleep(duration, sentinel):
#     """Like time.sleep, but checks a threading.Event sentinel every second.
#
#     Timing will not be all that accurate.
#
#     Args:
#         duration: integer.
#         sentinel: threading.Event instance.
#     """
#     int_dur, r_dur = divmod(duration, 1)
#     int_dur = int(int_dur)
#     for i in range(int_dur):
#         if not sentinel.is_set():
#             return
#         time.sleep(1)
#     time.sleep(r_dur)
#
#
# if __name__ == "__main__":
#     print(binary_search([-2, 1], 0, not_found="nearest"))
#     pass
