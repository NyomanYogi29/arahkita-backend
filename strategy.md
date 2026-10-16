# 🧭 Dokumen Strategi Integrasi & Arsitektur Frontend ArahKita

Dokumen ini adalah panduan teknis dan strategi integrasi antara **ArahKita Frontend** (React + Vite, Vanilla JavaScript, IndexedDB/Dexie.js) dan **ArahKita Backend** (Stateless AI Gateway).

Dokumen ini memuat arsitektur *offline-first*, skema penyimpanan lokal browser, siklus hidup pengerjaan trial, serta **informasi perubahan arsitektur terbaru** (khususnya input mata pelajaran dinamis dan evaluasi kecocokan).

---

## 📌 Daftar Isi
1. [Ringkasan Perubahan Terbaru (Changelog)](#1-ringkasan-perubahan-terbaru-changelog)
2. [Prinsip Arsitektur (Stateless Backend + Offline-First Frontend)](#2-prinsip-arsitektur)
3. [Desain Database Lokal: IndexedDB (Dexie.js)](#3-desain-database-lokal-indexeddb-dexiejs)
4. [Alur Siklus Hidup & Sinkronisasi Data](#4-alur-siklus-hidup--sinkronisasi-data)
5. [Implementasi Layanan & Helper Frontend](#5-implementasi-layanan--helper-frontend)
   - [5.1. Setup Database Dexie (`src/db/index.js`)](#51-setup-database-dexie-srcdbindexjs)
   - [5.2. Penyimpanan Profil Onboarding Dinamis](#52-penyimpanan-profil-onboarding-dinamis)
   - [5.3. Pengerjaan Soal Pilihan Ganda (Offline-First)](#53-pengerjaan-soal-pilihan-ganda-offline-first)
   - [5.4. Pengerjaan Soal Esai Reflektif (Real-time AI Evaluator)](#54-pengerjaan-soal-esai-reflektif-real-time-ai-evaluator)
   - [5.5. Agregasi Metrik & Generate Preview Rangkuman](#55-agregasi-metrik--generate-preview-rangkuman)
   - [5.6. Pengambilan Leaderboard Akhir](#56-pengambilan-leaderboard-akhir)
6. [Formula Kalkulasi Persentase Kecocokan Backend](#6-formula-kalkulasi-persentase-kecocokan-backend)

---

## 1. ⚡ Ringkasan Perubahan Terbaru (Changelog)

Bagi tim frontend, perhatikan pembaruan arsitektur berikut:

### 1.1. Input Mata Pelajaran Menjadi Dinamis Penuh
- **Sebelumnya**: Field `nilai` mengharuskan 3 mata pelajaran kaku (`Matematika`, `IPA`, `Bahasa_Inggris`).
- **Sekarang**: Siswa dapat menginput mata pelajaran peminatan apapun (misal `"Fisika"`, `"Kimia"`, `"Biologi"`, `"Sosiologi"`, `"Ekonomi"`, `"Geografi"`, `"Informatika"`, dsb.) sesuai kurikulum SMA/SMK mereka.
- **Batasan Validasi**:
  - **Minimal 3** dan **maksimal 10** mata pelajaran.
  - Setiap mata pelajaran memiliki skor integer antara **0 hingga 100**.
  - Tidak ada mata pelajaran wajib tertentu (siswa memilih mapel yang paling mereka percaya diri).
- **Normalisasi Lowercase Otomatis**:
  - Backend otomatis mengubah seluruh nama mapel menjadi huruf kecil murni (*lowercase*) dan memotong spasi (`key.strip().lower()`), misal `"Fisika"` $\to$ `"fisika"`, `"  KIMIA  "` $\to$ `"kimia"`.
  - Duplikasi nama mapel setelah normalisasi (misal `"Fisika"` dan `"fisika"` dikirim bersamaan) akan ditolak validasi.

### 1.2. Relevansi Mata Pelajaran pada Leaderboard Mengikuti Input Dinamis
- Endpoint `POST /api/v1/recommendation-results` mengekstrak kandidat mata pelajaran relevan langsung dari daftar nilai dinamis yang siswa kirimkan di `profile.nilai`.
- Properti `subject_name` pada badge `subject_relevances` dikembalikan dalam bentuk **lowercase** murni (contoh: `"fisika"`, `"biologi"`). Frontend dapat mengatur format visual tampilan (misal menggunakan CSS `text-transform: capitalize`).
- Dibatasi minimal 1 hingga maksimal 3 mata pelajaran paling relevan per jurusan.

### 1.3. Penomoran Node Trial Dimulai dari Nomor 2
- Nomor urut node minicase dari backend (`minicase_number`) dimulai dari **2 hingga 11**.
- Nomor **1** dialokasikan khusus untuk panduan pengerjaan (*Rules Pengerjaan*) yang dikelola langsung oleh frontend di state lokal.

### 1.4. Path Parameter Endpoint Preview
- Endpoint preview jurusan menggunakan path parameter: `POST /api/v1/preview/{major_node_id}`.

---

## 2. 🧠 Prinsip Arsitektur

```text
┌──────────────────────────────────────────────┐
│        Frontend (React + Vite, Offline)      │
│  - Form Onboarding (Dinamis 3-10 Mapel)       │
│  - Local Rules Card (Node #1)                │
│  - IndexedDB (Dexie.js) Local Storage        │
│  - Instant MCQ Evaluation (Offline)          │
│  - Metrik Agregasi Lokal                     │
└──────────────────────┬───────────────────────┘
                       │ HTTP / JSON (HTTPS)
                       ▼
┌──────────────────────────────────────────────┐
│        Backend (Stateless AI Gateway)        │
│  - Rekomendasi Jurusan Awal (LLM)            │
│  - Generator Soal Trial (Pohon Node 2-11)    │
│  - AI Evaluator Esai Reflektif (1-5 Skor)    │
│  - Generator Preview Naratif & Karir Realistis│
│  - Leaderboard Sorter + Subject Relevances   │
└──────────────────────────────────────────────┘
```

1. **Stateless Backend**:
   - Backend tidak menyimpan database pengguna atau state pengerjaan di server.
   - Bertindak murni sebagai **AI Processing & Scoring Gateway**.
2. **Offline-First Frontend**:
   - Seluruh status progres (`is_done`, pilihan jawaban, hasil evaluasi esai sementara) disimpan di **IndexedDB browser** menggunakan wrapper [Dexie.js](https://dexie.org/).
   - Siswa dapat keluar dari aplikasi, menutup tab browser, atau berganti halaman tanpa kehilangan progres pengerjaan trial.

---

## 3. 🗄️ Desain Database Lokal: IndexedDB (Dexie.js)

Gunakan 4 Object Store utama pada database lokal `ArahKitaDB`:

| Object Store | Primary Key | Indeks Kunci | Keterangan & Isi Data |
| :--- | :--- | :--- | :--- |
| `profile` | `++id` *(auto)* | - | Menyimpan input minat & nilai rapor awal siswa dari onboarding (berisi mapel dinamis). |
| `majors` | `id` *(UUID)* | `major_name` | Menyimpan daftar rekomendasi jurusan (`MajorNode`). |
| `minicases` | `id` *(UUID)* | `parent_id, minicase_number, is_done, node_type` | Rantai soal studi kasus trial beserta jawaban & status pengerjaan siswa. |
| `previews` | `id` *(UUID)* | `major_node_id, matching_percentage` | Rangkuman evaluasi AI, persentase kecocokan, dan kartu karir tiap jurusan yang telah selesai. |

---

## 4. 🔄 Alur Siklus Hidup & Sinkronisasi Data

```mermaid
flowchart TD
    A["1. Onboarding Survey (3-10 Mapel)"] -->|POST /api/v1/majors/recommend| B["Simpan profile & majors di IndexedDB"]
    B --> C["2. Siswa Memilih 1 Jurusan"]
    C -->|POST /api/v1/minicases/generate| D["Simpan minicases (Nomor 2 s.d. 11) di IndexedDB"]
    D --> E["3. Tampilkan Node #1: Rules Pengerjaan (Lokal)"]
    E --> F{"4. Pengerjaan Soal (Node #2 s.d. #11)"}
    
    F -->|Node Multiple Choice| G["Evaluasi Lokal Instan\n(user_answer == correct_answer)\nUpdate minicase di IndexedDB"]
    F -->|Node Essay| H["POST /api/v1/minicases/evaluate-essay\nSimpan skor analitis & minat di IndexedDB"]
    
    G --> I{"Semua Trial Selesai?"}
    H --> I
    I -->|Belum| F
    I -->|Ya| J["5. Agregasi Metrik Performa Lokal\n(calculateMajorMetrics)"]
    
    J -->|POST /api/v1/preview/{major_id}| K["Terima MajorNodePreview & Karir\nSimpan ke store previews di IndexedDB"]
    K --> L["6. Buka Halaman Leaderboard"]
    L -->|POST /api/v1/recommendation-results| M["Leaderboard Terurut + Badge Mapel Relevan"]
```

---

## 5. 💻 Implementasi Layanan & Helper Frontend

### 5.1. Setup Database Dexie (`src/db/index.js`)

Instalasi dependency di frontend:
```bash
npm install dexie
```

Inisialisasi database:
```javascript
import Dexie from 'dexie';

export const db = new Dexie('ArahKitaDB');

// Definisikan skema dan indeks
db.version(1).stores({
  profile: '++id',
  majors: 'id, major_name',
  minicases: 'id, parent_id, minicase_number, is_done, node_type',
  previews: 'id, major_node_id, matching_percentage',
});
```

---

### 5.2. Penyimpanan Profil Onboarding Dinamis

Saat siswa mengirimkan survei minat dan daftar nilai mata pelajaran:

```javascript
import { db } from './db';
import { getMajorRecommendations } from './services/majorService';

export async function handleOnboardingSubmit(minatText, subjectList) {
  // 1. Bentuk key-value dictionary untuk field nilai
  // Contoh subjectList: [{ name: "Matematika", score: 85 }, { name: "Fisika", score: 80 }, { name: "Kimia", score: 90 }]
  const nilaiDict = {};
  for (const item of subjectList) {
    if (item.name.trim()) {
      nilaiDict[item.name.trim()] = Number(item.score);
    }
  }

  const payload = {
    minat: minatText.trim(),
    nilai: nilaiDict,
  };

  // 2. Request rekomendasi jurusan ke backend
  const majors = await getMajorRecommendations(payload);

  // 3. Simpan profil & jurusan ke IndexedDB lokal
  await db.transaction('rw', db.profile, db.majors, async () => {
    await db.profile.clear();
    await db.profile.add(payload);

    await db.majors.clear();
    await db.majors.bulkAdd(majors);
  });

  return majors;
}
```

---

### 5.3. Pengerjaan Soal Pilihan Ganda (Offline-First)

Karena kunci jawaban (`correct_answer`) sudah tersedia di objek `MinicaseNode`, evaluasi soal pilihan ganda berjalan secara **instan dan offline** tanpa melakukan panggilan jaringan:

```javascript
import { db } from './db';

export async function submitMultipleChoiceAnswer(minicaseId, selectedOption) {
  const node = await db.minicases.get(minicaseId);
  if (!node) throw new Error('Node trial tidak ditemukan.');

  const isCorrect = selectedOption.trim() === node.correct_answer.trim();

  // Update status lokal di IndexedDB
  await db.minicases.update(minicaseId, {
    user_answer: selectedOption,
    is_correct: isCorrect,
    is_done: true,
    updated_at: new Date().toISOString(),
  });

  return { isCorrect };
}
```

---

### 5.4. Pengerjaan Soal Esai Reflektif (Real-time AI Evaluator)

Teks jawaban esai siswa dikirimkan ke endpoint evaluasi esai backend untuk mendapatkan skor psikometrik:

```javascript
import { db } from './db';
import { evaluateEssayAnswer } from './services/minicaseService';

export async function submitEssayAnswer(node, userText) {
  // 1. Evaluasi real-time via AI backend
  const evalResult = await evaluateEssayAnswer({
    question: node.question,
    evaluation_hint: node.evaluation_hint,
    user_answer: userText.trim(),
    minicase_id: node.id,
  });
  // evalResult: { analytical_fit: 4, interest_signal: 5, is_serious_attempt: true }

  // 2. Simpan skor & status ke IndexedDB lokal
  await db.minicases.update(node.id, {
    user_answer: userText.trim(),
    analytical_fit: evalResult.analytical_fit,
    interest_signal: evalResult.interest_signal,
    is_serious_attempt: evalResult.is_serious_attempt,
    is_done: true,
    updated_at: new Date().toISOString(),
  });

  return evalResult;
}
```

---

### 5.5. Agregasi Metrik & Generate Preview Rangkuman

Ketika semua node trial pada suatu jurusan telah selesai dikerjakan (`is_done === true`), frontend menghitung rekapitulasi performa lokal dan memanggil endpoint preview:

```javascript
import { db } from './db';
import { getMajorPreview } from './services/previewService';

/**
 * Menghitung metrik agregat dari trial yang telah diselesaikan di IndexedDB.
 */
export async function calculateMajorMetrics(majorId) {
  const nodes = await db.minicases.where({ parent_id: majorId, is_done: true }).toArray();

  const mcqNodes = nodes.filter((n) => n.node_type === 'multiple_choice');
  const essayNodes = nodes.filter((n) => n.node_type === 'essay');

  // 1. Akurasi MCQ (0 - 100%)
  const correctCount = mcqNodes.filter((n) => n.is_correct === true).length;
  const mcqAccuracy = mcqNodes.length > 0 ? (correctCount / mcqNodes.length) * 100 : 0;

  // 2. Rata-rata Skor Daya Analitis Esai (skala 1.0 - 5.0)
  const totalAnalytical = essayNodes.reduce((sum, n) => sum + (n.analytical_fit || 1), 0);
  const avgAnalytical = essayNodes.length > 0 ? totalAnalytical / essayNodes.length : 3.0;

  // 3. Rata-rata Skor Sinyal Minat Esai (skala 1.0 - 5.0)
  const totalInterest = essayNodes.reduce((sum, n) => sum + (n.interest_signal || 1), 0);
  const avgInterest = essayNodes.length > 0 ? totalInterest / essayNodes.length : 3.0;

  return {
    mcq_accuracy: Number(mcqAccuracy.toFixed(1)),
    essay_analytical_score: Number(avgAnalytical.toFixed(2)),
    essay_interest_score: Number(avgInterest.toFixed(2)),
    total_trials_completed: nodes.length,
  };
}

/**
 * Sinkronisasi metrik ke backend untuk mendapatkan teks preview & rekomendasi karir.
 */
export async function generateAndSavePreview(major, userRating = null) {
  const metrics = await calculateMajorMetrics(major.id);
  const profileRecord = await db.profile.toCollection().first();

  const payload = {
    major_name: major.major_name,
    mcq_accuracy: metrics.mcq_accuracy,
    essay_analytical_score: metrics.essay_analytical_score,
    essay_interest_score: metrics.essay_interest_score,
    total_trials_completed: metrics.total_trials_completed,
    user_satisfaction_rating: userRating,
    profile: profileRecord || null,
  };

  // Panggil endpoint: POST /api/v1/preview/{major_id}
  const previewData = await getMajorPreview(major.id, payload);

  // Simpan hasil preview ke IndexedDB
  await db.previews.put({
    ...previewData,
    major_node_id: major.id,
  });

  return previewData;
}
```

---

### 5.6. Pengambilan Leaderboard Akhir

Saat membuka halaman Leaderboard, frontend mengambil data dari IndexedDB lokal dan mengirimkannya ke `POST /api/v1/recommendation-results`:

```javascript
import { db } from './db';
import { getRecommendationResults } from './services/recommendationService';

export async function fetchLeaderboardFromLocal() {
  const [majorNodes, previews, profile] = await Promise.all([
    db.majors.toArray(),
    db.previews.toArray(),
    db.profile.toCollection().first(),
  ]);

  const results = await getRecommendationResults({
    major_nodes: majorNodes,
    previews: previews,
    profile: profile || null,
  });

  return results;
}
```

---

## 6. 📐 Formula Kalkulasi Persentase Kecocokan Backend

Backend menghitung persentase kecocokan keminatan menggunakan bobot terukur (*deterministic weighted scoring*):

$$\text{Matching \%} = \text{round}\left( 0.30 \times \text{MCQ} + 0.35 \times \left(\frac{\text{Analitis}}{5} \times 100\right) + 0.35 \times \left(\frac{\text{Minat}}{5} \times 100\right) \right)$$

### Rincian Pembobotan:
1. **30% Akurasi MCQ (`mcq_accuracy`)**:
   - Menguji penguasaan konsep dasar dan pemahaman awal materi pengantar jurusan.
2. **35% Kemampuan Analitis Esai (`essay_analytical_score`)**:
   - Menguji logika pemecahan masalah (*problem-solving*), penalaran kritis, dan struktur penyelesaian kasus.
3. **35% Sinyal Minat Esai (`essay_interest_score`)**:
   - Menguji antusiasme, rasa ingin tahu intelektual, dan resiliensi siswa dalam menghadapi tantangan studi kasus.
4. **Batas Nilai Akhir (*Clamping*)**:
   - Nilai dibulatkan ke bilangan bulat terdekat dan di-*clamp* secara aman pada rentang **`1%` s.d. `100%`**.
