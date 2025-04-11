export default {
  async fetch(request, env, ctx) {
    // Forward the request to the Python worker
    const response = await env.PYTHON_WORKER.fetch(request);
    return response;
  },
};