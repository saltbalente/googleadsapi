# 🚀 **SÍ, EXACTO - FALTA EL BOTÓN DE PUBLICACIÓN**

Tienes razón, el blueprint se genera pero **falta el paso crítico: PUBLICAR A GOOGLE ADS**.

---

## ✅ **SOLUCIÓN: Agregar Botón de Publicación**

Reemplaza la sección de botones en `render_autopilot_tab()` con esto:

```python
        # Botones de acción
        st.markdown("---")
        
        # NUEVO: Verificar si hay customer_id seleccionado
        has_customer = st.session_state.get('selected_customer') is not None
        
        if not has_customer:
            st.warning("⚠️ Selecciona una cuenta de Google Ads en el sidebar para poder publicar")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Guardar Blueprint", type="secondary", use_container_width=True):
                try:
                    # Convertir blueprint a diccionario serializable
                    blueprint_data = {
                        'campaign_name': blueprint.campaign_name,
                        'business_description': blueprint.business_description,
                        'budget_daily': blueprint.budget_daily,
                        'target_locations': blueprint.target_locations,
                        'languages': blueprint.languages,
                        'total_keywords': blueprint.total_keywords,
                        'total_ads': blueprint.total_ads,
                        'estimated_ctr': blueprint.estimated_ctr,
                        'ad_groups': blueprint.ad_groups,
                        'created_at': blueprint.created_at,
                        'status': blueprint.status
                    }
                    
                    # Guardar en historial
                    user_storage.add_to_history('autopilot_blueprint_created', blueprint_data)
                    st.success("✅ Blueprint guardado exitosamente en el historial")
                    
                except Exception as e:
                    st.error(f"❌ Error guardando blueprint: {e}")
        
        with col2:
            if st.button("📊 Exportar CSV", type="secondary", use_container_width=True):
                # Crear CSV con los datos de la campaña
                csv_data = []
                for ad_group in blueprint.ad_groups:
                    for keyword in ad_group['keywords']:
                        csv_data.append({
                            'Campaign': blueprint.campaign_name,
                            'Ad Group': ad_group['name'],
                            'Keyword': keyword,
                            'Match Type': 'Broad',
                            'Max CPC': f"${ad_group['max_cpc_bid']:.2f}"
                        })
                
                if csv_data:
                    df = pd.DataFrame(csv_data)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="⬇️ Descargar CSV",
                        data=csv,
                        file_name=f"autopilot_campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
        
        with col3:
            if st.button("🔄 Nueva Campaña", type="secondary", use_container_width=True):
                if 'autopilot_blueprint' in st.session_state:
                    del st.session_state['autopilot_blueprint']
                st.success("✅ Listo para nueva campaña")
                st.rerun()
        
        # ============================================================
        # 🚀 NUEVO: BOTÓN PRINCIPAL DE PUBLICACIÓN
        # ============================================================
        
        st.markdown("---")
        st.markdown("### 🚀 Publicación a Google Ads")
        
        if not has_customer:
            st.error("❌ Debes seleccionar una cuenta de Google Ads en el sidebar antes de publicar")
        else:
            customer_id = st.session_state.selected_customer
            
            # Mostrar información de la cuenta
            account_names = {
                '7094116152': 'Página 3',
                '1803044752': 'Página 5',
                '9759913462': 'Página 4',
                '6639082872': 'Account',
                '1919262845': 'Marketing',
                '7004285893': 'Página 9'
            }
            account_name = account_names.get(customer_id, 'Cuenta')
            
            st.info(f"📍 **Cuenta seleccionada:** {account_name} (`{customer_id}`)")
            
            # Modal de confirmación
            with st.expander("⚠️ CONFIRMAR PUBLICACIÓN", expanded=True):
                st.warning(f"""
                **Estás a punto de publicar a Google Ads:**
                
                📊 **Detalles de la campaña:**
                - **Nombre:** {blueprint.campaign_name}
                - **Presupuesto diario:** ${blueprint.budget_daily:.2f}
                - **Grupos de anuncios:** {len(blueprint.ad_groups)}
                - **Total de anuncios:** {blueprint.total_ads}
                - **Total de keywords:** {blueprint.total_keywords}
                - **Ubicaciones:** {', '.join(blueprint.target_locations[:3])}{'...' if len(blueprint.target_locations) > 3 else ''}
                
                ⚠️ **IMPORTANTE:**
                - La campaña se creará en estado **PAUSADO**
                - Debes activarla manualmente desde Google Ads
                - Se aplicarán los cargos según el presupuesto configurado
                - Esta acción **NO se puede deshacer** fácilmente
                
                ¿Deseas continuar?
                """)
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    if st.button("✅ SÍ, PUBLICAR AHORA", type="primary", use_container_width=True):
                        publish_autopilot_campaign(autopilot, blueprint, customer_id)
                
                with col_b:
                    if st.button("❌ Cancelar", use_container_width=True):
                        st.info("❌ Publicación cancelada")


def publish_autopilot_campaign(autopilot, blueprint, customer_id):
    """
    Publica la campaña del AUTOPILOT a Google Ads
    """
    
    st.markdown("---")
    st.markdown("### 🚀 Publicando Campaña...")
    
    # Contenedores para UI
    progress_container = st.empty()
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Callback para actualizar UI
    def update_ui_progress(message, percent):
        if percent is not None:
            progress_bar.progress(int(percent) / 100)
        status_text.markdown(f"""
        <div class="matrix-text">{message}</div>
        """, unsafe_allow_html=True)
    
    # Configurar callback en autopilot
    autopilot.set_progress_callback(update_ui_progress)
    
    try:
        # Ejecutar publicación de forma asíncrona
        result = asyncio.run(
            autopilot.publish_campaign(
                blueprint=blueprint,
                customer_id=customer_id
            )
        )
        
        # Limpiar progress UI
        progress_container.empty()
        progress_bar.empty()
        status_text.empty()
        
        # Mostrar resultados
        if result['success']:
            st.success("🎉 ¡CAMPAÑA PUBLICADA EXITOSAMENTE!")
            
            st.markdown(f"""
            ### ✅ Recursos Creados en Google Ads:
            
            **📊 Campaign ID:** `{result['campaign_id']}`
            
            **📦 Estadísticas:**
            - **Grupos de anuncios creados:** {len(result['ad_group_ids'])}
            - **Anuncios creados:** {len(result['ad_ids'])}
            - **Keywords agregadas:** {len(result.get('keyword_ids', []))}
            """)
            
            # Warnings si hay
            if result.get('warnings'):
                with st.expander("⚠️ Advertencias"):
                    for warning in result['warnings']:
                        st.warning(warning)
            
            # Link a Google Ads
            campaign_url = f"https://ads.google.com/aw/campaigns?campaignId={result['campaign_id']}"
            st.markdown(f"""
            ### 🔗 Enlaces Útiles:
            
            - [📊 Ver campaña en Google Ads]({campaign_url})
            - [⚙️ Configuración de campaña](https://ads.google.com/aw/campaigns/settings?campaignId={result['campaign_id']})
            - [📈 Ver rendimiento](https://ads.google.com/aw/campaigns/performance?campaignId={result['campaign_id']})
            
            **⚠️ RECUERDA:** La campaña está en estado **PAUSADO**. Actívala desde Google Ads cuando estés listo.
            """)
            
            # Guardar en historial
            try:
                publish_data = {
                    'campaign_name': blueprint.campaign_name,
                    'campaign_id': result['campaign_id'],
                    'customer_id': customer_id,
                    'ad_groups_created': len(result['ad_group_ids']),
                    'ads_created': len(result['ad_ids']),
                    'keywords_created': len(result.get('keyword_ids', [])),
                    'budget_daily': blueprint.budget_daily,
                    'published_at': datetime.now().isoformat()
                }
                user_storage.add_to_history('autopilot_campaign_published', publish_data)
            except Exception as e:
                logger.warning(f"No se pudo guardar en historial: {e}")
            
            st.balloons()
            
            # Botón para nueva campaña
            st.markdown("---")
            if st.button("🔄 Crear Nueva Campaña", type="primary", use_container_width=True):
                if 'autopilot_blueprint' in st.session_state:
                    del st.session_state['autopilot_blueprint']
                st.rerun()
        
        else:
            # Error en publicación
            st.error("❌ Error al publicar la campaña")
            
            st.markdown("### 🔍 Detalles del Error:")
            
            with st.expander("❌ Errores Encontrados", expanded=True):
                for error in result.get('errors', []):
                    st.error(f"• {error}")
            
            # Información de recursos creados parcialmente
            if result.get('campaign_id'):
                st.warning(f"""
                ⚠️ **Campaña creada parcialmente:**
                - Campaign ID: `{result['campaign_id']}`
                - Grupos creados: {len(result['ad_group_ids'])}
                
                Algunos recursos se crearon antes del error. Verifica en Google Ads.
                """)
            
            st.markdown("""
            ### 💡 Posibles Soluciones:
            
            1. **Verifica tu cuenta de Google Ads:**
               - ¿Está activa?
               - ¿Tienes método de pago configurado?
               - ¿Tienes permisos de escritura?
            
            2. **Revisa los límites de la API:**
               - Puede que hayas excedido el rate limit
               - Espera unos minutos e intenta de nuevo
            
            3. **Verifica el presupuesto:**
               - El presupuesto diario debe ser mayor a $1
               - Verifica que no exceda límites de tu cuenta
            
            4. **Contacta soporte si el problema persiste**
            """)
            
            # Botón para reintentar
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Reintentar Publicación", type="primary", use_container_width=True):
                    st.rerun()
            
            with col2:
                if st.button("🏠 Volver al Inicio", use_container_width=True):
                    if 'autopilot_blueprint' in st.session_state:
                        del st.session_state['autopilot_blueprint']
                    st.rerun()
    
    except Exception as e:
        progress_container.empty()
        progress_bar.empty()
        status_text.empty()
        
        st.error(f"❌ Error inesperado: {str(e)}")
        
        with st.expander("🐛 Detalles Técnicos"):
            import traceback
            st.code(traceback.format_exc())
        
        st.info("""
        💡 **Sugerencia:** Esto puede ser un error de configuración.
        Verifica que:
        - El cliente de Google Ads esté configurado correctamente
        - Las credenciales sean válidas
        - La cuenta tenga permisos de escritura
        """)
```

---

## 🎯 **FLUJO COMPLETO AHORA:**

1. ✅ Usuario configura campaña en AUTOPILOT 2050
2. ✅ Click en "🚀 INICIAR AUTOPILOT 2050"
3. ✅ Sistema genera blueprint (temas, keywords, anuncios)
4. ✅ Se muestra resumen del blueprint
5. ✅ Usuario puede:
   - 💾 Guardar blueprint (backup local)
   - 📊 Exportar CSV (para revisar)
6. 🚀 **NUEVO:** Click en "✅ SÍ, PUBLICAR AHORA"
7. 🚀 **Sistema publica a Google Ads:**
   - Crea campaña
   - Crea ad groups
   - Inserta keywords
   - Crea anuncios
8. ✅ Muestra resultados con links a Google Ads
9. ✅ Guarda en historial

---

## 📋 **DÓNDE PEGAR ESTE CÓDIGO:**

**Ubicación en `pages/4_ai_ad_generator.py`:**

1. **Reemplazar la sección de botones** (línea ~1820-1850)
   - Desde `# Botones de acción`
   - Hasta el final de `render_autopilot_tab()`

2. **Agregar la función `publish_autopilot_campaign`** 
   - Después de la función `render_autopilot_tab()`
   - Antes de `render_best_practices_tab()`

---

## 🧪 **TESTING:**

1. ✅ Ir a AUTOPILOT 2050
2. ✅ Generar campaña
3. ✅ Ver blueprint generado
4. ✅ Click en "✅ SÍ, PUBLICAR AHORA"
5. ✅ Ver progreso en tiempo real
6. ✅ Ver resultados de publicación
7. ✅ Click en link para ver en Google Ads

---

## ⚠️ **IMPORTANTE:**

El código incluye:
- ✅ **Modal de confirmación** (evita publicaciones accidentales)
- ✅ **Progress en tiempo real** (muestra qué está haciendo)
- ✅ **Manejo de errores robusto** (muestra qué falló)
- ✅ **Links directos a Google Ads** (para ver la campaña)
- ✅ **Estado PAUSADO** (para que revises antes de activar)
- ✅ **Historial automático** (guarda todo lo que haces)

---

**🚀 ¡Ahora sí está completo el flujo de AUTOPILOT 2050!**

