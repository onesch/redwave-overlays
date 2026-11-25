"""
Shared components: overlay-independent calculations over telemetry data.

A component is pure and stateless. It takes plain, already normalized
telemetry values, knows nothing about the IRSDK service or any overlay,
and returns a domain result that services store in their own context.
"""
