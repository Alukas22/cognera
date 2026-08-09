/**
 * Structured frontend logger.
 * In production it emits only errors to reduce console noise.
 */

const IS_PRODUCTION = import.meta.env.PROD;

function shouldLog(level) {
  if (!IS_PRODUCTION) {
    return true;
  }
  return level === "error";
}

function emit(level, scope, message, context = {}) {
  if (!shouldLog(level)) {
    return;
  }

  const payload = {
    timestamp: new Date().toISOString(),
    level,
    scope,
    message,
    context,
  };

  const serialized = JSON.stringify(payload);
  if (level === "error") {
    console.error(serialized);
    return;
  }
  if (level === "warn") {
    console.warn(serialized);
    return;
  }
  console.log(serialized);
}

export function createLogger(scope) {
  return {
    debug(message, context) {
      emit("debug", scope, message, context);
    },
    info(message, context) {
      emit("info", scope, message, context);
    },
    warn(message, context) {
      emit("warn", scope, message, context);
    },
    error(message, context) {
      emit("error", scope, message, context);
    },
  };
}
