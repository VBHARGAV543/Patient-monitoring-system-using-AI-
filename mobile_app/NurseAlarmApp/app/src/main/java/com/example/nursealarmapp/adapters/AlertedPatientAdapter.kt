package com.example.nursealarmapp.adapters

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import androidx.cardview.widget.CardView
import androidx.recyclerview.widget.RecyclerView
import com.example.nursealarmapp.R
import com.example.nursealarmapp.models.GeneralPatient

/**
 * Shows the ALERTED list (max 3 patients at a time).
 * Each row: vitals summary + "Cam" button + "Attended" button.
 */
class AlertedPatientAdapter(
    private var patients: List<GeneralPatient>,
    private val onPatientClick: (GeneralPatient) -> Unit,
    private val onAttended: (GeneralPatient) -> Unit,
    private val onCam: (GeneralPatient) -> Unit = {}
) : RecyclerView.Adapter<AlertedPatientAdapter.VH>() {

    class VH(view: View) : RecyclerView.ViewHolder(view) {
        val card: CardView    = view.findViewById(R.id.cardAlerted)
        val avatar: TextView  = view.findViewById(R.id.tvAltAvatar)
        val name: TextView    = view.findViewById(R.id.tvAltName)
        val disease: TextView = view.findViewById(R.id.tvAltDisease)
        val risk: TextView    = view.findViewById(R.id.tvAltRisk)
        val hr: TextView      = view.findViewById(R.id.tvAltHR)
        val spo2: TextView    = view.findViewById(R.id.tvAltSpO2)
        val bp: TextView      = view.findViewById(R.id.tvAltBP)
        val temp: TextView    = view.findViewById(R.id.tvAltTemp)
        val rr: TextView      = view.findViewById(R.id.tvAltRR)
        val time: TextView    = view.findViewById(R.id.tvAltTime)
        val btnAttended: Button = view.findViewById(R.id.btnAttended)
        val btnCam: Button      = view.findViewById(R.id.btnCam)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
        val v = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_alerted_patient, parent, false)
        return VH(v)
    }

    override fun onBindViewHolder(holder: VH, position: Int) {
        val p = patients[position]

        holder.avatar.text = p.name.firstOrNull()?.uppercase() ?: "P"
        holder.name.text = p.name
        holder.disease.text = p.disease
        holder.risk.text = p.riskLevel
        holder.risk.setBackgroundColor(
            if (p.riskLevel == "HIGH") 0xFFF44336.toInt() else 0xFFFF9800.toInt()
        )

        holder.hr.text   = "❤  HR: ${p.heartRate} bpm"
        holder.spo2.text = "🫁 SpO₂: ${p.spO2}%"
        holder.bp.text   = "💉 BP: ${p.bpSystolic}/${p.bpDiastolic}"
        holder.temp.text = "🌡 Temp: ${"%.1f".format(p.temperature)}°C"
        holder.rr.text   = "〰 RR: ${p.respRate} rpm"
        holder.time.text = "⏰ ${p.alertTimestamp}"

        holder.card.setOnClickListener { onPatientClick(p) }
        holder.btnAttended.setOnClickListener { onAttended(p) }
        holder.btnCam.setOnClickListener { onCam(p) }
    }

    override fun getItemCount() = patients.size

    fun update(newList: List<GeneralPatient>) {
        patients = newList
        notifyDataSetChanged()
    }
}
