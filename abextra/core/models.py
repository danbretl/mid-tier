def queryset_by_unique_fields(model_instance, exclude=None):
    """follows in spirit and the word of regular Model._perform_unique_checks"""
    unique_checks, date_checks = model_instance._get_unique_checks(exclude=exclude)

    for model_class, unique_check in unique_checks:
        # Try to look up an existing object with the same values as this
        # object's values for all the unique field.

        lookup_kwargs = {}
        for field_name in unique_check:
            f = model_instance._meta.get_field(field_name)
            lookup_value = getattr(model_instance, f.attname)
            if lookup_value is None:
                # no value, skip the lookup
                continue
            if f.primary_key and not model_instance._state.adding:
                # no need to check for unique primary key when editing
                continue
            lookup_kwargs[str(field_name)] = lookup_value

        # some fields were skipped, no reason to do the check
        if len(unique_check) != len(lookup_kwargs.keys()):
            continue

        qs = model_class._default_manager.filter(**lookup_kwargs)

        # Exclude the current object from the query if we are editing an
        # instance (as opposed to creating a new one)
        if not model_instance._state.adding and model_instance.pk is not None:
            qs = qs.exclude(pk=model_instance.pk)

        return qs
