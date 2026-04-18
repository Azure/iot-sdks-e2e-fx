// Licensed to the .NET Foundation under one or more agreements.
// The .NET Foundation licenses this file to you under the MIT license.
// See the LICENSE file in the project root for more information.

namespace System.Diagnostics.Tracing
{
    public sealed class ConsoleEventListener : EventListener
    {
        private readonly string[] _eventFilters;
        private object _lock = new object();
        private bool _isHandlingEvent = false;

        public ConsoleEventListener() : this(string.Empty) { }

        public ConsoleEventListener(string filter)
        {
            _eventFilters = new string[1];
            _eventFilters[0] = filter ?? throw new ArgumentNullException(nameof(filter));

            InitializeEventSources();
        }

        public ConsoleEventListener(string [] filters)
        {
            _eventFilters = filters ?? throw new ArgumentNullException(nameof(filters));
            if (_eventFilters.Length == 0) throw new ArgumentException("Filters cannot be empty");

            foreach (string filter in _eventFilters)
            {
                if (string.IsNullOrWhiteSpace(filter))
                {
                    throw new ArgumentNullException(nameof(filters));
                }
            }

            InitializeEventSources();
        }

        private void InitializeEventSources()
        {
            foreach (EventSource source in EventSource.GetSources())
            {
                // Only subscribe to sources matching our filters
                foreach (string filter in _eventFilters)
                {
                    if (source.Name.StartsWith(filter))
                    {
                        EnableEvents(source, EventLevel.LogAlways);
                        break;
                    }
                }
            }
        }

        protected override void OnEventSourceCreated(EventSource eventSource)
        {
            base.OnEventSourceCreated(eventSource);

            // Only enable events for sources that match our filters to avoid
            // recursive event storms from subscribing to ALL EventSources.
            if (_eventFilters == null) return;
            foreach (string filter in _eventFilters)
            {
                if (eventSource.Name.StartsWith(filter))
                {
#if NET451
                    EnableEvents(eventSource, EventLevel.LogAlways);
#else
                    EnableEvents(eventSource, EventLevel.LogAlways, EventKeywords.All);
#endif
                    return;
                }
            }
        }

        protected override void OnEventWritten(EventWrittenEventArgs eventData)
        {
            if (_eventFilters == null) return;

            lock (_lock)
            {
                // Prevent infinite recursion: Console.WriteLine can trigger
                // additional EventSource events, which re-enter OnEventWritten.
                if (_isHandlingEvent) return;
                _isHandlingEvent = true;
                try
                {
                    bool shouldDisplay = false;
            
                if (_eventFilters.Length == 1 && eventData.EventSource.Name.StartsWith(_eventFilters[0]))
                {
                    shouldDisplay = true;
                }
                else
                {
                    foreach (string filter in _eventFilters)
                    {
                        if (eventData.EventSource.Name.StartsWith(filter))
                        {
                            shouldDisplay = true;
                        }
                    }
                }

                if (shouldDisplay)
                {
#if NET451
                    string text = $"{DateTime.Now.ToString("yyyy-MM-ddTHH:mm:ss.fffffff")} [{eventData.EventSource.Name}-{eventData.EventId}]{(eventData.Payload != null ? $" ({string.Join(", ", eventData.Payload)})." : "")}";
#else
                    string text = $"{DateTime.Now.ToString("yyyy-MM-ddTHH:mm:ss.fffffff")} [{eventData.EventSource.Name}-{eventData.EventName}]{(eventData.Payload != null ? $" ({string.Join(", ", eventData.Payload)})." : "")}";
#endif

                    ConsoleColor origForeground = Console.ForegroundColor;
                    Console.ForegroundColor = ConsoleColor.DarkYellow;
                    Console.WriteLine(text);
                    Debug.WriteLine(text);
                    Console.ForegroundColor = origForeground;
                }
                }
                finally
                {
                    _isHandlingEvent = false;
                }
            }
        }
    }
}
