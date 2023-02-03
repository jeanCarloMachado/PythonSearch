from python_search.events.run_performed.clean import RunPerformedCleaning


class EventsEtl:
    """
    An aggregation of ETLS of events to be used as cli
    """

    def clean_events_performed(self):
        RunPerformedCleaning().clean()


def main():
    import fire

    fire.Fire(EventsEtl)


if __name__ == "__main__":
    main()
