package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/mux"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

type ServiceInfo struct {
	ID       string    `json:"id"`
	Name     string    `json:"name"`
	Address  string    `json:"address"`
	Status   string    `json:"status"`
	LastSeen time.Time `json:"last_seen"`
}

type Runtime struct {
	mu       sync.RWMutex
	services map[string]ServiceInfo
}

func NewRuntime() *Runtime {
	return &Runtime{
		services: make(map[string]ServiceInfo),
	}
}

func (r *Runtime) RegisterService(w http.ResponseWriter, req *http.Request) {
	var info ServiceInfo
	if err := json.NewDecoder(req.Body).Decode(&info); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	r.mu.Lock()
	defer r.mu.Unlock()

	if info.ID == "" {
		info.ID = uuid.New().String()
	}
	info.LastSeen = time.Now()
	info.Status = "UP"
	r.services[info.ID] = info

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(info)
	log.Printf("Service registered: %s (%s)", info.Name, info.ID)
}

func (r *Runtime) ListServices(w http.ResponseWriter, req *http.Request) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	var list []ServiceInfo
	for _, s := range r.services {
		list = append(list, s)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(list)
}

func (r *Runtime) HealthCheck(w http.ResponseWriter, req *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("OK"))
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8000"
	}

	runtime := NewRuntime()
	router := mux.NewRouter()

	router.HandleFunc("/health", runtime.HealthCheck).Methods("GET")
	router.HandleFunc("/login", LoginHandler).Methods("POST")

	// Secured routes
	api := router.PathPrefix("/api/v1").Subrouter()
	api.Use(AuthMiddleware)
	api.HandleFunc("/services", runtime.ListServices).Methods("GET")
	api.HandleFunc("/services/register", runtime.RegisterService).Methods("POST")

	router.Handle("/metrics", promhttp.Handler())

	srv := &http.Server{
		Handler:      router,
		Addr:         fmt.Sprintf("0.0.0.0:%s", port),
		WriteTimeout: 15 * time.Second,
		ReadTimeout:  15 * time.Second,
	}

	log.Printf("ExplainAI-Sentinel Runtime starting on port %s", port)
	log.Fatal(srv.ListenAndServe())
}
