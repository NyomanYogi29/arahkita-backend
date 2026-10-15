# 📖 Panduan API ArahKita Backend

Dokumentasi resmi kontrak antarmuka API (*API Contract*) antara **ArahKita Backend** dan **ArahKita Frontend** (React + Vite, JavaScript). Dokumen ini dirancang modular agar setiap penambahan endpoint baru dapat dengan mudah ditambahkan di bagian bawah.

---

## 📌 Daftar Isi
1. [Konfigurasi Lingkungan & Base URL](#1-konfigurasi-lingkungan--base-url)
2. [Format Standar Error Response](#2-format-standar-error-response)
3. [Daftar Endpoint](#3-daftar-endpoint)
   - [3.1. POST /api/v1/majors/recommend](#31-post-apiv1majorsrecommend)
   - [3.2. POST /api/v1/recommendation-results](#32-post-apiv1recommendation-results)
4. [Contoh Implementasi Frontend (React + Vite)](#4-contoh-implementasi-frontend-react--vite)
   - [4.1. File Service: src/services/majorService.js](#41-file-service-srcservicesmajorservicejs)
   - [4.2. File Service: src/services/recommendationService.js](#42-file-service-srcservicesrecommendationservicejs)
   - [4.3. Komponen Form Onboarding: src/components/OnboardingSurvey.jsx](#43-komponen-form-onboarding-srccomponentsonboardingsurveyjsx)
   - [4.4. Komponen Leaderboard: src/components/RecommendationLeaderboard.jsx](#44-komponen-leaderboard-srccomponentsrecommendationleaderboardjsx)

---

## 1. Konfigurasi Lingkungan & Base URL

Backend ArahKita telah aktif dan di-hosting secara publik dengan protokol HTTPS di:
- **Production Base URL**: `https://api.nyomanyogi.my.id/api/v1`
- **Development (Local) Base URL**: `http://localhost:8000/api/v1`
- **Health Check**: `https://api.nyomanyogi.my.id/health`

Di project **React + Vite**, buat atau tambahkan variabel lingkungan pada file `.env`:

```env
# URL dasar backend ArahKita (Production)
VITE_API_BASE_URL=https://api.nyomanyogi.my.id/api/v1

# Untuk pengembangan lokal (opsional):
# VITE_API_BASE_URL=http://localhost:8000/api/v1
```

> 💡 **Catatan CORS & HTTPS**: Backend sudah mendukung HTTPS dan mengizinkan `allow_origins=["*"]`, sehingga frontend React + Vite (baik saat running di `localhost:5173` maupun setelah dideploy ke Vercel/Netlify/GitHub Pages) dapat langsung berkomunikasi secara aman tanpa kendala Mixed Content ataupun CORS.

---

## 2. Format Standar Error Response

Backend menggunakan FastAPI dan Pydantic v2. Format pesan error mengikuti standar berikut:

### 2.1. Validasi Input Gagal (`422 Unprocessable Entity`)
Terjadi jika format JSON salah, tipe data tidak sesuai, atau ada batas nilai yang dilanggar.
```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["body", "nilai", "Matematika"],
      "msg": "Input should be less than or equal to 100",
      "input": 105,
      "ctx": {
        "le": 100
      }
    }
  ]
}
```

### 2.2. Kesalahan Server / LLM (`500 Internal Server Error`)
Terjadi jika OpenRouter/LLM mengalami gangguan atau output tidak dapat diparsing.
```json
{
  "detail": "Internal Server Error"
}
```

---

## 3. Daftar Endpoint

---

### 3.1. `POST /api/v1/majors/recommend`

#### 🎯 Deskripsi
Menganalisis minat serta nilai mata pelajaran akhir siswa (`Matematika`, `IPA`, `Bahasa_Inggris`), kemudian menghasilkan **2 hingga 6 pilihan rekomendasi jurusan kuliah** dalam bentuk visual node (`MajorNode`).

Node-node ini siap disimpan ke dalam state frontend atau SQLite lokal untuk mendukung kapabilitas offline.

---

#### 🌐 HTTP Request
- **Method**: `POST`
- **URL**: `${VITE_API_BASE_URL}/majors/recommend` (atau `https://api.nyomanyogi.my.id/api/v1/majors/recommend`)
- **Headers**:
  ```http
  Content-Type: application/json
  Accept: application/json
  ```

---

#### 📥 Request Body
Berupa JSON object sesuai skema `InputKeminatan`:

| Field | Tipe Data | Wajib | Keterangan & Validasi |
| :--- | :--- | :--- | :--- |
| `minat` | `string` | Ya | Teks deskripsi minat, hobi, atau bakat siswa (minimal 1 karakter). |
| `nilai` | `object` | Ya | Objek berisi skor 3 mata pelajaran utama. |
| `nilai.Matematika` | `integer` | Ya | Nilai angka mata pelajaran Matematika (rentang `0` s.d. `100`). |
| `nilai.IPA` | `integer` | Ya | Nilai angka mata pelajaran IPA (rentang `0` s.d. `100`). |
| `nilai.Bahasa_Inggris` | `integer` | Ya | Nilai angka mata pelajaran Bahasa Inggris (rentang `0` s.d. `100`). Perhatikan penggunaan underscore `_`. |

##### Contoh Request Payload:
```json
{
  "minat": "Saya suka merakit komputer, bermain logika puzzle, dan tertarik membuat game serta kecerdasan buatan.",
  "nilai": {
    "Matematika": 88,
    "IPA": 82,
    "Bahasa_Inggris": 90
  }
}
```

---

#### 📤 Response Body (Success: `200 OK`)
Mengembalikan **JSON Array** berisi 2 hingga 6 objek `MajorNode`.

##### Struktur Field Tiap `MajorNode`:
| Field | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | `string` | UUID v4 unik untuk identifikasi node (contoh: `e4b1a2c3-...`). |
| `major_name` | `string` | Nama resmi jurusan kuliah dalam bahasa Indonesia (contoh: `"Teknik Informatika"`). |
| `circle_color` | `string` | Kode hex warna lingkaran kurasi untuk visualisasi UI (contoh: `"#4F46E5"`). |
| `child_id` | `string` atau `null` | UUID node anak pertama (bernilai `null` pada tahap inisiasi ini, akan terisi saat pohon minicase dibuat). |

##### Contoh Response Payload (`200 OK`):
```json
[
  {
    "id": "7b8d4f6c-8519-4a0b-8d77-16d2f31a1001",
    "major_name": "Teknik Informatika",
    "circle_color": "#4F46E5",
    "child_id": null
  },
  {
    "id": "9a3e2b10-72c4-48f1-bfa6-28e4a90b2002",
    "major_name": "Sistem Informasi",
    "circle_color": "#06B6D4",
    "child_id": null
  },
  {
    "id": "3c5f8e12-61d9-4b7e-9082-37f5d81c3003",
    "major_name": "Sains Data",
    "circle_color": "#10B981",
    "child_id": null
  },
  {
    "id": "1d8a4b90-50e8-46a2-a1f7-49a6c72d4004",
    "major_name": "Teknologi Game",
    "circle_color": "#F59E0B",
    "child_id": null
  }
]
```

---

#### ⚠️ Kemungkinan Respon Error

##### Kasus 1: Nilai Melebihi Batas (`422 Unprocessable Entity`)
- **Kondisi**: Ada skor yang kurang dari 0 atau lebih dari 100.
```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["body", "nilai", "Matematika"],
      "msg": "Input should be less than or equal to 100",
      "input": 120,
      "ctx": {
        "le": 100
      }
    }
  ]
}
```

##### Kasus 2: Minat Dibiarkan Kosong (`422 Unprocessable Entity`)
- **Kondisi**: String `minat` dikirim berupa string kosong `""`.
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "minat"],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {
        "min_length": 1
      }
    }
  ]
}
```

##### Kasus 3: Kunci Objek Salah Tulis (`422 Unprocessable Entity`)
- **Kondisi**: Menuliskan `"Bahasa Inggris"` (menggunakan spasi) bukan `"Bahasa_Inggris"` (menggunakan underscore).
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "nilai", "Bahasa_Inggris"],
      "msg": "Field required",
      "input": {
        "Matematika": 80,
        "IPA": 85,
        "Bahasa Inggris": 90
      }
    }
  ]
}
```

##### Kasus 4: Kesalahan Jaringan / Server Backend (`500 Internal Server Error`)
- **Kondisi**: Terjadi kendala koneksi ke LLM OpenRouter atau kuota habis.
```json
{
  "detail": "Gagal mem-parsing rekomendasi jurusan dari LLM: ..."
}
```

---

### 3.2. `POST /api/v1/recommendation-results`

#### 🎯 Deskripsi
Menyusun dan mengurutkan peringkat (*leaderboard*) rekomendasi jurusan siswa berdasarkan `matching_percentage` dari nilai tertinggi ke terendah secara *descending*.

Endpoint ini menggabungkan:
1. **`major_nodes`**: Daftar seluruh jurusan rekomendasi awal yang tersimpan di SQLite lokal / state frontend pengguna.
2. **`previews`**: Daftar hasil evaluasi trial jurusan yang telah diselesaikan oleh siswa (memuat skor kecocokan, narasi preview, dan jalur karir).
3. **`profile`** *(opsional)*: Data minat dan nilai rapor siswa dari onboarding.

##### Aturan Bisnis & Perilaku Backend:
- **Jurusan yang Selesai (`is_completed: true`)**:
  - `matching_percentage` diambil dari preview hasil trial (jika terdapat beberapa preview untuk jurusan yang sama, diambil skor tertinggi).
  - Objek `preview` lengkap dilampirkan (termasuk narasi rangkuman dan 1–4 `career_paths`).
  - Backend mengevaluasi 1 hingga 3 badge mata pelajaran SMA/SMK yang paling relevan (`subject_relevances`) secara cerdas via LLM jika profil nilai siswa disertakan.
- **Jurusan yang Belum Dikerjakan (`is_completed: false`)**:
  - `matching_percentage` otomatis bernilai `0`.
  - `preview` bernilai `null` dan `subject_relevances` berupa array kosong `[]`.
  - Secara otomatis diurutkan di bagian bawah *leaderboard*.
- **Toleransi Gangguan (Graceful Fallback)**: Jika LLM gagal saat mengevaluasi relevansi mata pelajaran, backend tetap berhasil mengembalikan response `200 OK` dengan melakukan fallback otomatis ke mata pelajaran dengan nilai tertinggi siswa.

---

#### 🌐 HTTP Request
- **Method**: `POST`
- **URL**: `${VITE_API_BASE_URL}/recommendation-results` (atau `https://api.nyomanyogi.my.id/api/v1/recommendation-results`)
- **Headers**:
  ```http
  Content-Type: application/json
  Accept: application/json
  ```

---

#### 📥 Request Body
Berupa JSON object sesuai skema `RecommendationResultsRequest`:

| Field | Tipe Data | Wajib | Keterangan & Validasi |
| :--- | :--- | :--- | :--- |
| `major_nodes` | `array` of `MajorNode` | Ya | Daftar semua node jurusan rekomendasi yang ada di lokal pengguna (bisa `[]`). |
| `previews` | `array` of `MajorNodePreview` | Ya | Daftar objek preview hasil trial yang telah diselesaikan (bisa `[]`). |
| `profile` | `object` (`InputKeminatan`) atau `null` | Tidak | Profil minat dan nilai siswa dari onboarding (opsional, digunakan untuk analisis badge mapel relevan). |

##### Contoh Request Payload:
```json
{
  "major_nodes": [
    {
      "id": "7b8d4f6c-8519-4a0b-8d77-16d2f31a1001",
      "major_name": "Teknik Informatika",
      "circle_color": "#4F46E5",
      "child_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
    },
    {
      "id": "9a3e2b10-72c4-48f1-bfa6-28e4a90b2002",
      "major_name": "Sistem Informasi",
      "circle_color": "#06B6D4",
      "child_id": null
    }
  ],
  "previews": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "major_node_id": "7b8d4f6c-8519-4a0b-8d77-16d2f31a1001",
      "preview": "Kamu menunjukkan potensi analitis dan ketertarikan yang sangat tinggi dalam pemecahan masalah komputasi serta logika algoritma.",
      "matching_percentage": 92,
      "career_paths": [
        {
          "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
          "major_node_preview_id": "550e8400-e29b-41d4-a716-446655440000",
          "title": "Software Engineer",
          "detail": "Merancang, mengembangkan, dan memelihara arsitektur perangkat lunak skala besar serta sistem aplikasi modern."
        },
        {
          "id": "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
          "major_node_preview_id": "550e8400-e29b-41d4-a716-446655440000",
          "title": "AI Specialist",
          "detail": "Membangun model machine learning dan kecerdasan buatan untuk otomatisasi cerdas."
        }
      ]
    }
  ],
  "profile": {
    "minat": "Saya suka merakit komputer, bermain logika puzzle, dan tertarik membuat game serta kecerdasan buatan.",
    "nilai": {
      "Matematika": 88,
      "IPA": 82,
      "Bahasa_Inggris": 90
    }
  }
}
```

---

#### 📤 Response Body (Success: `200 OK`)
Mengembalikan **JSON Array** berisi objek `MajorRecommendationResult` yang telah diurutkan dari skor `matching_percentage` tertinggi ke terendah.

##### Struktur Field Tiap `MajorRecommendationResult`:
| Field | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | `string` | UUID v4 node jurusan (`major_node_id`). |
| `major_name` | `string` | Nama jurusan rekomendasi. |
| `circle_color` | `string` | Kode hex warna lingkaran (`#4F46E5`). |
| `child_id` | `string` atau `null` | UUID node anak pertama minicase (jika ada). |
| `matching_percentage` | `integer` | Persentase kecocokan keminatan (`0` s.d. `100`). Bernilai `0` jika jurusan belum selesai dikerjakan. |
| `is_completed` | `boolean` | `true` jika siswa telah menyelesaikan trial jurusan ini, `false` jika belum. |
| `preview` | `object` atau `null` | Objek detail preview lengkap (narasi & karir) jika `is_completed: true`, atau `null` jika belum. |
| `subject_relevances` | `array` | Daftar 1 hingga 3 badge mata pelajaran SMA/SMK yang paling relevan untuk jurusan tersebut. |

##### Struktur Objek `subject_relevances`:
| Field | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | `string` | UUID v4 unik badge relevansi. |
| `major_node_id` | `string` | UUID v4 jurusan terkait. |
| `subject_name` | `string` | Nama mata pelajaran relevan (misal: `"Matematika"`, `"Bahasa Inggris"`, `"IPA"`). |

##### Contoh Response Payload (`200 OK`):
```json
[
  {
    "id": "7b8d4f6c-8519-4a0b-8d77-16d2f31a1001",
    "major_name": "Teknik Informatika",
    "circle_color": "#4F46E5",
    "child_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
    "matching_percentage": 92,
    "is_completed": true,
    "preview": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "major_node_id": "7b8d4f6c-8519-4a0b-8d77-16d2f31a1001",
      "preview": "Kamu menunjukkan potensi analitis dan ketertarikan yang sangat tinggi dalam pemecahan masalah komputasi serta logika algoritma.",
      "matching_percentage": 92,
      "career_paths": [
        {
          "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
          "major_node_preview_id": "550e8400-e29b-41d4-a716-446655440000",
          "title": "Software Engineer",
          "detail": "Merancang, mengembangkan, dan memelihara arsitektur perangkat lunak skala besar serta sistem aplikasi modern."
        },
        {
          "id": "6ba7b811-9dad-11d1-80b4-00c04fd430c8",
          "major_node_preview_id": "550e8400-e29b-41d4-a716-446655440000",
          "title": "AI Specialist",
          "detail": "Membangun model machine learning dan kecerdasan buatan untuk otomatisasi cerdas."
        }
      ]
    },
    "subject_relevances": [
      {
        "id": "c3a1d95e-1823-4e44-88aa-32b04f128011",
        "major_node_id": "7b8d4f6c-8519-4a0b-8d77-16d2f31a1001",
        "subject_name": "Matematika"
      },
      {
        "id": "f8c2b74a-9311-419b-bb12-91e84a203922",
        "major_node_id": "7b8d4f6c-8519-4a0b-8d77-16d2f31a1001",
        "subject_name": "Bahasa Inggris"
      }
    ]
  },
  {
    "id": "9a3e2b10-72c4-48f1-bfa6-28e4a90b2002",
    "major_name": "Sistem Informasi",
    "circle_color": "#06B6D4",
    "child_id": null,
    "matching_percentage": 0,
    "is_completed": false,
    "preview": null,
    "subject_relevances": []
  }
]
```

---

#### ⚠️ Kemungkinan Respon Error

##### Kasus 1: Format UUID Tidak Valid (`422 Unprocessable Entity`)
- **Kondisi**: ID node bukan UUID v4 yang sah.
```json
{
  "detail": [
    {
      "type": "string_pattern_mismatch",
      "loc": ["body", "major_nodes", 0, "id"],
      "msg": "String should match pattern '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'",
      "input": "bukan-uuid"
    }
  ]
}
```

##### Kasus 2: Nilai Persentase Preview di Luar Rentang (`422 Unprocessable Entity`)
- **Kondisi**: Objek preview dikirim dengan `matching_percentage` bernilai negatif atau melebihi 100.
```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["body", "previews", 0, "matching_percentage"],
      "msg": "Input should be less than or equal to 100",
      "input": 150
    }
  ]
}
```

##### Kasus 3: Kesalahan Server Backend (`500 Internal Server Error`)
- **Kondisi**: Terjadi kesalahan internal yang tidak tertangani di backend.
```json
{
  "detail": "Internal Server Error"
}
```

---

## 4. Contoh Implementasi Frontend (React + Vite)

### 4.1. File Service: `src/services/majorService.js`

```javascript
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api.nyomanyogi.my.id/api/v1';

/**
 * Mengirim survei minat dan nilai siswa untuk mendapatkan rekomendasi jurusan kuliah.
 * 
 * @param {Object} payload
 * @param {string} payload.minat - Deskripsi minat siswa
 * @param {Object} payload.nilai - Objek nilai siswa
 * @param {number} payload.nilai.Matematika - Skor Matematika (0-100)
 * @param {number} payload.nilai.IPA - Skor IPA (0-100)
 * @param {number} payload.nilai.Bahasa_Inggris - Skor Bahasa Inggris (0-100)
 * @returns {Promise<Array<{ id: string, major_name: string, circle_color: string, child_id: string|null }>>}
 */
export async function getMajorRecommendations(payload) {
  try {
    const response = await fetch(`${BASE_URL}/majors/recommend`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      
      if (response.status === 422) {
        const errorMessages = errorData?.detail
          ? errorData.detail.map((err) => `${err.loc.join('.')}: ${err.msg}`).join(', ')
          : 'Validasi form tidak valid.';
        throw new Error(`Validasi Gagal: ${errorMessages}`);
      }

      const serverMessage = errorData?.detail || 'Terjadi kesalahan pada server backend.';
      throw new Error(`Error (${response.status}): ${serverMessage}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Gagal mengambil rekomendasi jurusan:', error);
    throw error;
  }
}
```

---

### 4.2. File Service: `src/services/recommendationService.js`

```javascript
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api.nyomanyogi.my.id/api/v1';

/**
 * Mengirim data major_nodes, previews yang telah diselesaikan, dan profil keminatan
 * untuk mendapatkan leaderboard rekomendasi jurusan beserta badge mata pelajaran relevan.
 * 
 * @param {Object} payload
 * @param {Array<Object>} payload.major_nodes - Daftar node jurusan dari local storage/state
 * @param {Array<Object>} payload.previews - Daftar preview hasil trial yang telah diselesaikan
 * @param {Object|null} [payload.profile] - Profil keminatan dan nilai awal siswa (opsional)
 * @returns {Promise<Array<Object>>} Daftar MajorRecommendationResult terurut descending
 */
export async function getRecommendationResults(payload) {
  try {
    const response = await fetch(`${BASE_URL}/recommendation-results`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);

      if (response.status === 422) {
        const errorMessages = errorData?.detail
          ? errorData.detail.map((err) => `${err.loc.join('.')}: ${err.msg}`).join(', ')
          : 'Format payload request tidak valid.';
        throw new Error(`Validasi Gagal: ${errorMessages}`);
      }

      const serverMessage = errorData?.detail || 'Terjadi kesalahan pada server backend.';
      throw new Error(`Error (${response.status}): ${serverMessage}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Gagal mengambil leaderboard rekomendasi:', error);
    throw error;
  }
}
```

---

### 4.3. Komponen Form Onboarding: `src/components/OnboardingSurvey.jsx`

```jsx
import React, { useState } from 'react';
import { getMajorRecommendations } from '../services/majorService';

export default function OnboardingSurvey({ onRecommendationsReceived }) {
  const [minat, setMinat] = useState('');
  const [matematika, setMatematika] = useState(80);
  const [ipa, setIpa] = useState(80);
  const [bahasaInggris, setBahasaInggris] = useState(80);

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);

    const payload = {
      minat: minat.trim(),
      nilai: {
        Matematika: Number(matematika),
        IPA: Number(ipa),
        Bahasa_Inggris: Number(bahasaInggris),
      },
    };

    try {
      const recommendations = await getMajorRecommendations(payload);
      // Simpan rekomendasi ke state parent atau SQLite lokal frontend
      if (onRecommendationsReceived) {
        onRecommendationsReceived(recommendations);
      }
    } catch (err) {
      setErrorMessage(err.message || 'Gagal terhubung ke server.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: 450, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 12 }}>
      <h3>Survei Keminatan & Nilai</h3>

      {errorMessage && (
        <div style={{ color: '#EF4444', backgroundColor: '#FEE2E2', padding: 8, borderRadius: 6 }}>
          {errorMessage}
        </div>
      )}

      <label>
        Minat / Ketertarikan:
        <textarea
          value={minat}
          onChange={(e) => setMinat(e.target.value)}
          placeholder="Ceritakan apa yang kamu sukai atau cita-citakan..."
          required
          rows={3}
          style={{ width: '100%' }}
        />
      </label>

      <label>
        Nilai Matematika (0–100):
        <input
          type="number"
          min="0"
          max="100"
          value={matematika}
          onChange={(e) => setMatematika(e.target.value)}
          required
          style={{ width: '100%' }}
        />
      </label>

      <label>
        Nilai IPA (0–100):
        <input
          type="number"
          min="0"
          max="100"
          value={ipa}
          onChange={(e) => setIpa(e.target.value)}
          required
          style={{ width: '100%' }}
        />
      </label>

      <label>
        Nilai Bahasa Inggris (0–100):
        <input
          type="number"
          min="0"
          max="100"
          value={bahasaInggris}
          onChange={(e) => setBahasaInggris(e.target.value)}
          required
          style={{ width: '100%' }}
        />
      </label>

      <button type="submit" disabled={isLoading} style={{ marginTop: 10, padding: 10 }}>
        {isLoading ? 'Menganalisis Keminatan AI...' : 'Dapatkan Rekomendasi Jurusan'}
      </button>
    </form>
  );
}
```

---

### 4.4. Komponen Leaderboard: `src/components/RecommendationLeaderboard.jsx`

```jsx
import React, { useEffect, useState } from 'react';
import { getRecommendationResults } from '../services/recommendationService';

export default function RecommendationLeaderboard({ majorNodes, previews, profile }) {
  const [leaderboard, setLeaderboard] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchLeaderboard() {
      if (!majorNodes || majorNodes.length === 0) return;

      setIsLoading(true);
      setError(null);

      try {
        const results = await getRecommendationResults({
          major_nodes: majorNodes,
          previews: previews || [],
          profile: profile || null,
        });
        setLeaderboard(results);
      } catch (err) {
        setError(err.message || 'Gagal memuat leaderboard.');
      } finally {
        setIsLoading(false);
      }
    }

    fetchLeaderboard();
  }, [majorNodes, previews, profile]);

  if (isLoading) {
    return <p>Menyusun peringkat rekomendasi jurusan...</p>;
  }

  if (error) {
    return <p style={{ color: '#EF4444' }}>{error}</p>;
  }

  return (
    <div style={{ maxWidth: 600, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
      <h2>🏆 Leaderboard Rekomendasi Jurusan</h2>
      {leaderboard.map((item, index) => (
        <div
          key={item.id}
          style={{
            border: '1px solid #E5E7EB',
            borderRadius: 8,
            padding: 16,
            borderLeft: `6px solid ${item.circle_color}`,
            backgroundColor: item.is_completed ? '#FFFFFF' : '#F9FAFB',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h4 style={{ margin: 0 }}>
              #{index + 1} {item.major_name}
            </h4>
            <span
              style={{
                fontWeight: 'bold',
                fontSize: '1.1rem',
                color: item.is_completed ? item.circle_color : '#9CA3AF',
              }}
            >
              {item.is_completed ? `${item.matching_percentage}%` : 'Belum Trial'}
            </span>
          </div>

          {/* Badge Relevansi Mata Pelajaran SMA/SMK */}
          {item.subject_relevances && item.subject_relevances.length > 0 && (
            <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.8rem', color: '#6B7280' }}>Mapel Relevan:</span>
              {item.subject_relevances.map((sr) => (
                <span
                  key={sr.id}
                  style={{
                    backgroundColor: '#EEF2FF',
                    color: '#4F46E5',
                    padding: '2px 8px',
                    borderRadius: 12,
                    fontSize: '0.75rem',
                    fontWeight: 600,
                  }}
                >
                  {sr.subject_name}
                </span>
              ))}
            </div>
          )}

          {/* Narasi Preview & Karir jika sudah selesai */}
          {item.preview && (
            <div style={{ marginTop: 12, fontSize: '0.9rem', color: '#374151' }}>
              <p style={{ margin: '0 0 8px 0' }}>{item.preview.preview}</p>
              {item.preview.career_paths?.length > 0 && (
                <div>
                  <strong>Jalur Karir: </strong>
                  {item.preview.career_paths.map((cp) => cp.title).join(', ')}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
```
