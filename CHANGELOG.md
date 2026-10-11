# Changelog

## 0.4.0 - 2026-08-31

### Added

- One durable RabbitMQ priority queue per Pynenc logical queue.
- Documented lossy normalization of Pynenc float priorities to RabbitMQ's
  native 0-255 integer range.
- Application-isolated physical queues on shared RabbitMQ virtual hosts.

### Changed

- Requires Pynenc 0.4.0 and Python 3.12 or newer.
