package com.example.nursealarmapp.adapters

import android.graphics.Color
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.cardview.widget.CardView
import androidx.recyclerview.widget.RecyclerView
import com.example.nursealarmapp.R
import com.example.nursealarmapp.models.Patient

class PatientAdapter(
    private var patients: List<Patient>,
    private val onPatientClick: (Patient) -> Unit
) : RecyclerView.Adapter<PatientAdapter.PatientViewHolder>() {

    class PatientViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val cardView: CardView = view.findViewById(R.id.cardPatient)
        val nameText: TextView = view.findViewById(R.id.tvPatientName)
        val statusText: TextView = view.findViewById(R.id.tvPatientStatus)
        val timestampText: TextView = view.findViewById(R.id.tvPatientTimestamp)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): PatientViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_patient, parent, false)
        return PatientViewHolder(view)
    }

    override fun onBindViewHolder(holder: PatientViewHolder, position: Int) {
        val patient = patients[position]
        
        holder.nameText.text = patient.name
        holder.statusText.text = patient.status
        holder.timestampText.text = patient.timestamp
        
        // Highlight if fall detected
        if (patient.fallDetected) {
            holder.cardView.setCardBackgroundColor(Color.parseColor("#2B2B2B"))
            holder.nameText.setTextColor(Color.parseColor("#D4AF37"))
            holder.statusText.setTextColor(Color.parseColor("#FF6B6B"))
        } else {
            holder.cardView.setCardBackgroundColor(Color.parseColor("#E8E8E8"))
            holder.nameText.setTextColor(Color.parseColor("#2B2B2B"))
            holder.statusText.setTextColor(Color.parseColor("#4CAF50"))
        }
        
        holder.cardView.setOnClickListener {
            onPatientClick(patient)
        }
    }

    override fun getItemCount() = patients.size

    fun updatePatients(newPatients: List<Patient>) {
        patients = newPatients
        notifyDataSetChanged()
    }
}
