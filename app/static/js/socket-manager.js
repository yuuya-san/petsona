/**
 * Socket.IO Manager for Real-Time Vote Updates
 * Handles WebSocket connections and vote count synchronization
 */

function createSharedSocket(forcePolling = false) {
  if (window.sharedSocket) {
    return window.sharedSocket;
  }

  if (typeof io === 'undefined') {
    return null;
  }

  const socketUrl = window.socketIoUrl || window.location.origin;
  const opts = {
    path: '/socket.io',
    transports: forcePolling ? ['polling'] : ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: 8,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 15000,
    randomizationFactor: 0.5,
    timeout: 20000,
    autoConnect: true,
    upgrade: !forcePolling,
    secure: window.location.protocol === 'https:',
  };

  const socket = io(socketUrl, opts);
  window.sharedSocket = socket;

  let pollingFallbackScheduled = false;

  socket.on('connect_error', (error) => {
    console.warn('Socket.IO connect error:', error);
    if (!forcePolling && !pollingFallbackScheduled) {
      pollingFallbackScheduled = true;
      console.warn('Socket.IO websocket failed; retrying with polling only.');
      socket.disconnect();
      window.sharedSocket = null;
      setTimeout(() => {
        window.getSharedSocket = createSharedSocket;
        window.sharedSocket = createSharedSocket(true);
      }, 500);
    }
  });

  socket.on('reconnect_error', (error) => {
    console.warn('Socket.IO reconnect error:', error);
  });

  socket.on('reconnect_failed', () => {
    console.warn('Socket.IO reconnection failed. No further reconnect attempts.');
  });

  return socket;
}

window.getSharedSocket = window.getSharedSocket || createSharedSocket;

class SocketManager {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.watchers = new Map(); // species_id -> callback function
    this.breedWatchers = new Map(); // breed_id -> callback function
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    // Disable debug logging for performance
    this.debugMode = false;
    this.init();
  }

  log(...args) {
    if (this.debugMode && window['console'] && typeof window['console']['log'] === 'function') {
      window['console']['log'](...args);
    }
  }

  /**
   * Initialize Socket.IO connection
   */
  init() {
    try {
      if (typeof io === 'undefined') {
        return;
      }

      this.socket = window.getSharedSocket();
      if (!this.socket) {
        return;
      }

      this.connected = this.socket.connected;
      this.setupEventHandlers();
    } catch (error) {
      console.warn('SocketManager init error:', error);
    }
  }

  /**
   * Setup Socket.IO event handlers
   */
  setupEventHandlers() {
    if (!this.socket) return;

    this.socket.off('connect');
    this.socket.off('disconnect');
    this.socket.off('error');
    this.socket.off('connection_response');
    this.socket.off('vote_update');
    this.socket.off('breed_vote_update');
    this.socket.off('watch_confirmed');
    this.socket.off('reconnect_attempt');
    this.socket.off('reconnect');

    // Connection established
    this.socket.on('connect', () => {
      this.connected = true;
      this.reconnectAttempts = 0;
      this.log('🔗 Socket.IO connected:', this.socket.id);
      
      // Re-register watchers after reconnection
      this.rewatchAllSpecies();
      this.rewatchAllBreeds();
      
      // Notify listeners that socket is ready
      window.dispatchEvent(new CustomEvent('socket-ready', { detail: this.socket }));
    });

    // Connection lost
    this.socket.on('disconnect', () => {
      this.connected = false;
      this.log('❌ Socket.IO disconnected');
    });

    // Server sent error
    this.socket.on('error', (error) => {
      this.log('❌ Socket.IO error:', error);
    });

    // Connection response
    this.socket.on('connection_response', (data) => {
      this.log('✅ Connection response:', data);
    });

    // Vote update from server
    this.socket.on('vote_update', (data) => {
      const { species_id, vote_count } = data;
      const key = String(species_id);
      this.log(`📡 Vote update received for species ${species_id}: ${vote_count} votes`);
      
      // Call registered callback for this species
      if (this.watchers.has(key)) {
        const callback = this.watchers.get(key);
        callback(vote_count);
      }
    });

    // Breed vote update from server
    this.socket.on('breed_vote_update', (data) => {
      const { breed_id, total_votes, voted, user_id } = data;
      const key = String(breed_id);
      this.log(`📡 Breed vote update received for breed ${breed_id}: ${total_votes} votes`);

      // Call registered callback for this breed
      if (this.breedWatchers.has(key)) {
        const callback = this.breedWatchers.get(key);
        callback(total_votes, voted, user_id);
      }
    });

    // Watch confirmation
    this.socket.on('watch_confirmed', (data) => {
      this.log('✅ Watch confirmed:', data);
    });

    // Reconnection attempt
    this.socket.on('reconnect_attempt', () => {
      this.reconnectAttempts++;
      this.log(`⏳ Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
    });

    // Reconnection successful
    this.socket.on('reconnect', () => {
      this.connected = true;
      this.reconnectAttempts = 0;
    });
  }

  /**
   * Register a watcher for a specific species
   * @param {number} speciesId - The species ID to watch
   * @param {function} callback - Function to call when vote count changes
   */
  watchSpecies(speciesId, callback) {
    const key = String(speciesId);
    if (!this.socket || !this.connected) {
      setTimeout(() => this.watchSpecies(speciesId, callback), 100);
      return;
    }

    // Store callback
    this.watchers.set(key, callback);

    // Notify server
    this.socket.emit('watch_species', { species_id: speciesId });
  }

  /**
   * Unregister a watcher for a specific species
   * @param {number} speciesId - The species ID to unwatch
   */
  unwatchSpecies(speciesId) {
    if (!this.socket) return;
    const key = String(speciesId);

    this.watchers.delete(key);
    this.socket.emit('unwatch_species', { species_id: speciesId });
  }

  /**
   * Re-watch all species after reconnection
   */
  rewatchAllSpecies() {
    for (const [speciesId, callback] of this.watchers.entries()) {
      this.socket.emit('watch_species', { species_id: speciesId });
    }
  }

  /**
   * Register a watcher for a specific breed
   * @param {number} breedId - The breed ID to watch
   * @param {function} callback - Function to call when vote count changes
   */
  watchBreed(breedId, callback) {
    const key = String(breedId);
    if (!this.socket || !this.connected) {
      setTimeout(() => this.watchBreed(breedId, callback), 100);
      return;
    }

    this.breedWatchers.set(key, callback);
  }

  /**
   * Unregister a watcher for a specific breed
   * @param {number} breedId - The breed ID to unwatch
   */
  unwatchBreed(breedId) {
    const key = String(breedId);
    this.breedWatchers.delete(key);
  }

  /**
   * Re-watch all breeds after reconnection
   */
  rewatchAllBreeds() {
    for (const [breedId, callback] of this.breedWatchers.entries()) {
      this.watchBreed(breedId, callback);
    }
  }

  /**
   * Check if socket is connected
   */
  isConnected() {
    return this.connected && this.socket && this.socket.connected;
  }

  /**
   * Manually disconnect
   */
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.connected = false;
    }
  }

  /**
   * Manually reconnect
   */
  reconnect() {
    if (this.socket) {
      this.socket.connect();
    }
  }
}

// Create global instance
const socketManager = new SocketManager();

// Expose manager globally for page scripts and compatibility
window.socketManager = socketManager;
window.socket = socketManager.socket;
